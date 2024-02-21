"""
Module for handling websocket connections.
"""
import logging
import os
import asyncio
import base64
import json
import uuid

import asyncpg
import black
import sqlfluff
from botocore.exceptions import ClientError
from fastapi import WebSocket, WebSocketDisconnect
from psycopg2 import Error as Psycopg2Error
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from canvas_service.base.notifier import notify_pg_channel
from canvas_service.controller.connected_user_controller import ConnectedUserController
from canvas_service.services.asset_service import get_aws_credentials
from canvas_service.services.executor_service import get_block_run_by_block_id
from canvas_service.utils.default_content import default_content
from canvas_service.utils.default_properties import default_properties
from canvas_service.config.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    POSTGRES_DB, POSTGRES_HOST,
    POSTGRES_PASSWORD, POSTGRES_PORT,
    POSTGRES_USERNAME, S3_BUCKET,
    CALL_EXECUTOR_SERVICE_FOR_BLOCK_RUN,
)
from canvas_service.controller.block import Blocks
from canvas_service.controller.canvas import Canvases
from canvas_service.database import AsyncSessionFactory, SessionLocal
from canvas_service.database.models import Executor
from canvas_service.database.models.block import Block
from canvas_service.database.models.canvas import Canvas
from canvas_service.database.models.edge import Edge
from canvas_service.database.models.layer import Layer
from canvas_service.database.models.connected_users import ConnectedUsers
from canvas_service.database.schemas.block import Block as BlockSchema
from canvas_service.database.schemas.edge import Edge as EdgeSchema
from canvas_service.database.schemas.layer_schema import LayerSchema
from canvas_service.database.schemas.validation_config import (
    BlockStatuses,
    BlockTypes,
    LayerTypes,
)
from canvas_service.utils.dag_util import DAGUtil, ZerveDAGException
from canvas_service.utils.ecs_utils import stop_task
from canvas_service.utils.fargate_util import FargateUtil
from canvas_service.utils.graph_layout import graph_layout
from canvas_service.utils.import_util import ImportUtil
from canvas_service.utils.languages.default_fargate_locator import get_default_fargate_executor
from canvas_service.utils.languages.language_lambda_util import LanguageLambdaUtil
from canvas_service.utils.s3_utils import (
    delete_by_prefix_s3,
    put_empty_file_in_s3,
)
from canvas_service.utils.auto_pipelines.sklearn_classification import ClassificationPipeline
from canvas_service.utils.auto_pipelines.sklearn_regression import RegressionPipeline
from canvas_service.utils.sqs_utils.sqs_sender import ZerveSqsSender
from canvas_service.services.user_service import get_organisation_for_canvas_internal
from canvas_service.permissions.permission_manager import PermissionManager
from canvas_service.services.metric_service import MetricService

logger = logging.getLogger(__name__)


class WebsocketHandler:
    """
    Class that handles websocket connections
    """

    def __init__(
        self,
        websocket: WebSocket,
        sqs_sender: ZerveSqsSender,
        canvas_id: str,
        user_id: str = None,
        user_email: str = None,
    ):
        self.db = self.get_db()
        try:
            self.canvas = self.db.get(Canvas, canvas_id)
        except SQLAlchemyError:
            self.canvas = None
        self.canvas_id = canvas_id
        self.websocket = websocket
        self.connection_id = uuid.uuid4()
        self.user_id = user_id
        self.user_email = user_email
        self.queue = asyncio.Queue()
        self.listener_ready = asyncio.Future()
        self.listener = asyncio.create_task(
            self.listen_channel(canvas_id)
        )
        if self.canvas and "PYTEST_CURRENT_TEST" not in os.environ:
            try:
                self.organization = get_organisation_for_canvas_internal(resource_id=self.canvas.project_id)
                self.organization_id = self.organization["id"]
            except KeyError:
                self.organization_id = None
        else:
            self.organization_id = None
        self.initialised = True
        self.permission_manager = PermissionManager()
        self.sqs_sender = sqs_sender
        self._metrics = MetricService()

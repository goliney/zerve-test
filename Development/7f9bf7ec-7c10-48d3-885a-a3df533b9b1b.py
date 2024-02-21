"""
Changed module for handling websocket connections.
"""
import logging
import os
import asyncio
import base64
import json
import uuid

import asyncpg
import black
import zerve

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
        self.user_id = user_id
        self.user_email = user_email
        self.queue = asyncio.Queue()
        self.listener_ready = asyncio.Future()
        self.listener = asyncio.create_task(
            self.listen_channel(canvas_id)
        )
        while True:
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

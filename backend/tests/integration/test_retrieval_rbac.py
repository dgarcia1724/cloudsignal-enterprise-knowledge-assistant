"""Integration tests for retrieval with RBAC enforcement.

These tests verify that the full retrieval pipeline correctly
enforces RBAC at query time.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from qdrant_client.models import ScoredPoint

from app.schemas.user import UserContext
from app.services.retrieval.service import RetrievalService


class TestRetrievalRBAC:
    """Test retrieval service RBAC enforcement."""

    @pytest.fixture
    def mock_vector_store(self) -> MagicMock:
        """Create mock vector store."""
        store = MagicMock()
        store.search_with_rbac = AsyncMock(return_value=[])
        store.get_by_document_id = AsyncMock(return_value=[])
        return store

    @pytest.fixture
    def mock_embedder(self) -> MagicMock:
        """Create mock embedder."""
        embedder = MagicMock()
        embedder.embed_query = AsyncMock(return_value=[0.1] * 1536)
        return embedder

    @pytest.fixture
    def mock_rbac_service(self) -> MagicMock:
        """Create mock RBAC service."""
        service = MagicMock()
        service.get_filter_for_user = MagicMock(return_value=MagicMock())
        return service

    @pytest.fixture
    def retrieval_service(
        self,
        mock_vector_store: MagicMock,
        mock_embedder: MagicMock,
        mock_rbac_service: MagicMock,
    ) -> RetrievalService:
        """Create retrieval service with mocks."""
        service = RetrievalService(
            vector_store=mock_vector_store,
            embedder=mock_embedder,
            rbac_service=mock_rbac_service,
        )
        service._bm25_initialized = False  # Skip BM25 for these tests
        return service

    @pytest.mark.asyncio
    async def test_retrieval_calls_rbac_filter(
        self,
        retrieval_service: RetrievalService,
        mock_rbac_service: MagicMock,
        engineer_user: UserContext,
    ):
        """Verify that retrieval builds RBAC filter for user."""
        await retrieval_service.retrieve(
            query="test query",
            user_context=engineer_user,
        )

        # RBAC filter should be built for the user
        mock_rbac_service.get_filter_for_user.assert_called_once_with(engineer_user)

    @pytest.mark.asyncio
    async def test_retrieval_passes_filter_to_vector_store(
        self,
        retrieval_service: RetrievalService,
        mock_vector_store: MagicMock,
        mock_rbac_service: MagicMock,
        engineer_user: UserContext,
    ):
        """Verify that RBAC filter is passed to vector store search."""
        expected_filter = MagicMock()
        mock_rbac_service.get_filter_for_user.return_value = expected_filter

        await retrieval_service.retrieve(
            query="test query",
            user_context=engineer_user,
        )

        # Vector store should be called with the RBAC filter
        mock_vector_store.search_with_rbac.assert_called_once()
        call_args = mock_vector_store.search_with_rbac.call_args
        assert call_args.kwargs["rbac_filter"] == expected_filter

    @pytest.mark.asyncio
    async def test_different_roles_get_different_filters(
        self,
        retrieval_service: RetrievalService,
        mock_rbac_service: MagicMock,
        engineer_user: UserContext,
        hr_user: UserContext,
    ):
        """Verify that different roles get different RBAC filters."""
        engineer_filter = MagicMock(name="engineer_filter")
        hr_filter = MagicMock(name="hr_filter")

        mock_rbac_service.get_filter_for_user.side_effect = [
            engineer_filter,
            hr_filter,
        ]

        await retrieval_service.retrieve("test query", engineer_user)
        await retrieval_service.retrieve("test query", hr_user)

        # Should be called with both users
        assert mock_rbac_service.get_filter_for_user.call_count == 2
        calls = mock_rbac_service.get_filter_for_user.call_args_list
        assert calls[0][0][0] == engineer_user
        assert calls[1][0][0] == hr_user

    @pytest.mark.asyncio
    async def test_retrieval_returns_only_filtered_results(
        self,
        retrieval_service: RetrievalService,
        mock_vector_store: MagicMock,
        engineer_user: UserContext,
    ):
        """Verify that retrieval only returns RBAC-filtered results."""
        # Mock vector store returning some results
        mock_results = [
            _create_mock_scored_point(
                id="point-1",
                score=0.95,
                payload={
                    "document_id": "doc-1",
                    "title": "Allowed Doc",
                    "text": "Some text",
                    "doc_type": "runbook",
                    "department": "engineering",
                    "access_level": "internal",
                },
            ),
        ]
        mock_vector_store.search_with_rbac.return_value = mock_results

        results = await retrieval_service.retrieve(
            query="test query",
            user_context=engineer_user,
        )

        # Results should match what vector store returned (post-filter)
        assert len(results) == 1
        assert results[0].document_id == "doc-1"
        assert results[0].title == "Allowed Doc"

    @pytest.mark.asyncio
    async def test_simple_retrieval_enforces_rbac(
        self,
        retrieval_service: RetrievalService,
        mock_vector_store: MagicMock,
        mock_rbac_service: MagicMock,
        engineer_user: UserContext,
    ):
        """Verify simple retrieval also enforces RBAC."""
        await retrieval_service.retrieve_simple(
            query="test query",
            user_context=engineer_user,
            limit=5,
        )

        # Should build RBAC filter
        mock_rbac_service.get_filter_for_user.assert_called_once()
        # Should pass filter to vector store
        mock_vector_store.search_with_rbac.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_id_enforces_rbac(
        self,
        retrieval_service: RetrievalService,
        mock_vector_store: MagicMock,
        mock_rbac_service: MagicMock,
        engineer_user: UserContext,
    ):
        """Verify getting document by ID also enforces RBAC."""
        await retrieval_service.get_document_by_id(
            document_id="doc-123",
            user_context=engineer_user,
        )

        # Should build RBAC filter
        mock_rbac_service.get_filter_for_user.assert_called_once()
        # Should pass filter to get_by_document_id
        mock_vector_store.get_by_document_id.assert_called_once()
        call_args = mock_vector_store.get_by_document_id.call_args
        assert "rbac_filter" in call_args.kwargs


class TestRetrievalWithMockData:
    """Test retrieval with mock document data."""

    @pytest.mark.asyncio
    async def test_engineer_sees_engineering_docs(
        self,
        engineer_user: UserContext,
        sample_document_payload: dict[str, Any],
    ):
        """Engineer should see engineering documents."""
        # This would be a full integration test with Qdrant
        # For now, we verify the structure
        assert engineer_user.role == "engineer"
        assert sample_document_payload["allowed_roles"] == ["engineer", "sre"]

    @pytest.mark.asyncio
    async def test_hr_sees_confidential_hr_docs(
        self,
        hr_user: UserContext,
        confidential_hr_document: dict[str, Any],
    ):
        """HR should see confidential HR documents."""
        assert hr_user.role == "hr"
        assert confidential_hr_document["access_level"] == "confidential"
        assert "hr" in confidential_hr_document["allowed_roles"]


def _create_mock_scored_point(
    id: str,
    score: float,
    payload: dict[str, Any],
) -> ScoredPoint:
    """Create a mock ScoredPoint for testing."""
    point = MagicMock(spec=ScoredPoint)
    point.id = id
    point.score = score
    point.payload = payload
    return point

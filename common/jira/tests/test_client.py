import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from common.jira.client import JiraApiClient
from common.jira.config import JiraConfig
from common.jira.exceptions import JiraError, JiraConnectionError, JiraAuthenticationError, JiraNotFoundError, JiraValidationError
from common.jira.models import JiraIssueModel, JiraTransition, JiraComment
import aiohttp

@pytest.fixture
def mock_config():
    return JiraConfig(
        JIRA_URL="https://test-jira.com",
        JIRA_API_TOKEN="test_token",
        API_VERSION="2",
        REQUEST_TIMEOUT=5,
        CACHE_TTL=300
    )

@pytest_asyncio.fixture
async def jira_client(mock_config):
    client = JiraApiClient(mock_config)
    await client.__aenter__()  # Инициализируем сессию
    yield client
    await client.__aexit__(None, None, None) # Закрываем сессию

@pytest.mark.asyncio
async def test_create_issue_success(jira_client):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {
            "key": "TEST-1",
            "id": "10000",
            "self": "https://test-jira.com/rest/api/2/issue/10000"
        }
        mock_post.return_value.__aenter__.return_value = mock_response

        with patch.object(jira_client, 'get_issue') as mock_get_issue:
            mock_get_issue.return_value = JiraIssueModel.from_raw_data({
                "key": "TEST-1",
                "fields": {
                    "summary": "Test Summary",
                    "description": "Test Description",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "testuser"},
                    "created": "2024-01-01T00:00:00.000+0000",
                    "updated": "2024-01-01T00:00:00.000+0000"
                }
            })

            issue_data = {
                "fields": {
                    "project": {"key": "TEST"},
                    "summary": "Test Summary",
                    "description": "Test Description",
                    "issuetype": {"id": "10001"},
                    "assignee": {"name": "testuser"}
                }
            }
            new_issue = await jira_client.create_issue(issue_data)

            mock_post.assert_called_once_with(
                f"{jira_client.base_url}/issue",
                json=issue_data,
                timeout=jira_client.config.REQUEST_TIMEOUT
            )
            mock_get_issue.assert_called_once_with("TEST-1")
            assert new_issue.key == "TEST-1"
            assert new_issue.summary == "Test Summary"

@pytest.mark.asyncio
async def test_create_issue_error(jira_client):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.reason = "Bad Request"
        mock_response.json.return_value = {"errorMessages": ["Invalid field"]}
        mock_post.return_value.__aenter__.return_value = mock_response

        issue_data = {
            "fields": {
                "project": {"key": "TEST"},
                "summary": "Invalid data",
                "issuetype": {"id": "invalid"}
            }
        }
        with pytest.raises(JiraError) as excinfo:
            await jira_client.create_issue(issue_data)
        assert "Не удалось получить ключ созданной задачи" in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_issue_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test Summary",
                "description": "Test Description",
                "status": {"name": "Open"},
                "assignee": {"displayName": "testuser"},
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-01T00:00:00.000+0000"
            }
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        issue = await jira_client.get_issue("TEST-1")

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/issue/TEST-1",
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert issue.key == "TEST-1"
        assert issue.summary == "Test Summary"

@pytest.mark.asyncio
async def test_get_issue_not_found(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        mock_response.json.return_value = {"errorMessages": ["Issue not found"]}
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=AsyncMock(),
            history=(),
            status=404,
            message="Not Found"
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        with pytest.raises(JiraNotFoundError):
            await jira_client.get_issue("NONEXISTENT-1")

@pytest.mark.asyncio
async def test_add_comment_success(jira_client):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"id": "12345"}
        mock_post.return_value.__aenter__.return_value = mock_response

        comment_data = await jira_client.add_comment("TEST-1", "This is a test comment.")

        mock_post.assert_called_once_with(
            f"{jira_client.base_url}/issue/TEST-1/comment",
            json={"body": "This is a test comment."},
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert comment_data["id"] == "12345"

@pytest.mark.asyncio
async def test_get_transitions_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "transitions": [
                {
                    "id": "1",
                    "name": "To Do",
                    "to": {
                        "self": "https://test-jira.com/rest/api/2/status/10001",
                        "description": "",
                        "iconUrl": "https://test-jira.com/images/icons/statuses/generic.png",
                        "name": "To Do",
                        "id": "10001",
                        "statusCategory": {
                            "self": "https://test-jira.com/rest/api/2/statuscategory/2",
                            "id": 2,
                            "key": "new",
                            "colorName": "blue-gray",
                            "name": "New"
                        }
                    }
                },
                {
                    "id": "2",
                    "name": "In Progress",
                    "to": {
                        "self": "https://test-jira.com/rest/api/2/status/10002",
                        "description": "",
                        "iconUrl": "https://test-jira.com/images/icons/statuses/inprogress.png",
                        "name": "In Progress",
                        "id": "10002",
                        "statusCategory": {
                            "self": "https://test-jira.com/rest/api/2/statuscategory/4",
                            "id": 4,
                            "key": "indeterminate",
                            "colorName": "yellow",
                            "name": "In Progress"
                        }
                    }
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        transitions = await jira_client.get_transitions("TEST-1")

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/issue/TEST-1/transitions",
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert len(transitions) == 2
        assert transitions[0].name == "To Do"
        assert transitions[1].id == "2"

@pytest.mark.asyncio
async def test_search_issues_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Summary 1",
                        "description": "Desc 1",
                        "status": {"name": "Done"},
                        "assignee": {"displayName": "user1"},
                        "created": "2024-01-01T00:00:00.000+0000",
                        "updated": "2024-01-01T00:00:00.000+0000"
                    }
                },
                {
                    "key": "TEST-2",
                    "fields": {
                        "summary": "Summary 2",
                        "description": "Desc 2",
                        "status": {"name": "In Progress"},
                        "assignee": {"displayName": "user2"},
                        "created": "2024-01-02T00:00:00.000+0000",
                        "updated": "2024-01-02T00:00:00.000+0000"
                    }
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        issues = await jira_client.search_issues("project=TEST", max_results=2)

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/search",
            params={'jql': 'project=TEST', 'maxResults': 2},
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert len(issues) == 2
        assert issues[0].key == "TEST-1"
        assert issues[1].summary == "Summary 2"

@pytest.mark.asyncio
async def test_get_issue_types_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"id": "10001", "name": "Bug"},
            {"id": "10002", "name": "Task"}
        ]
        mock_get.return_value.__aenter__.return_value = mock_response

        issue_types = await jira_client.get_issue_types()

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/issuetype",
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert len(issue_types) == 2
        assert issue_types[0]['name'] == "Bug"

@pytest.mark.asyncio
async def test_get_all_projects_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"id": "10000", "key": "PROJ1", "name": "Project One"},
            {"id": "10001", "key": "PROJ2", "name": "Project Two"}
        ]
        mock_get.return_value.__aenter__.return_value = mock_response

        projects = await jira_client.get_all_projects()

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/project",
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert len(projects) == 2
        assert projects[0]['key'] == "PROJ1"

@pytest.mark.asyncio
async def test_get_create_issue_metadata_success(jira_client):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "projects": [
                {
                    "key": "TEST",
                    "issuetypes": [
                        {"id": "10001", "name": "Bug", "fields": {"summary": {"required": True}}}
                    ]
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        metadata = await jira_client.get_create_issue_metadata(project_key="TEST")

        mock_get.assert_called_once_with(
            f"{jira_client.base_url}/issue/createmeta",
            params={'projectKeys': 'TEST'},
            timeout=jira_client.config.REQUEST_TIMEOUT
        )
        assert metadata["projects"][0]["key"] == "TEST"

@pytest.mark.asyncio
async def test_api_client_initialization_no_session(mock_config):
    client = JiraApiClient(mock_config)
    # Сессия не должна быть инициализирована без async with
    assert client.session is None

    with pytest.raises(JiraConnectionError) as excinfo:
        await client.get_all_projects()
    assert "Сессия не инициализирована" in str(excinfo.value) 
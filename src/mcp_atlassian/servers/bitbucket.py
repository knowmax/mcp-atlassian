"""Bitbucket FastMCP server instance and tool definitions."""

import json
import logging
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from pydantic import Field
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.servers.dependencies import get_bitbucket_fetcher
from mcp_atlassian.utils.decorators import check_write_access

logger = logging.getLogger(__name__)

bitbucket_mcp = FastMCP(name="Bitbucket MCP Service")


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def list_workspaces_or_projects(ctx: Context) -> str:
    """
    List all accessible workspaces (Cloud) or projects (Server/DC).

    Returns:
        JSON string containing list of workspaces/projects with their details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        workspaces = bitbucket.get_all_workspaces()
        workspace_dicts = [
            ws.model_dump(mode="json", serialize_as_any=True) for ws in workspaces
        ]

        return json.dumps(workspace_dicts, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = "An unexpected error occurred while fetching workspaces."
            logger.exception("Unexpected error in bitbucket_list_workspaces:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_workspaces failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def list_repositories(
    ctx: Context,
    workspace: Annotated[
        str | None,
        Field(
            description="Workspace name (Cloud) or project key (Server/DC). If not provided, lists all accessible repositories.",
            default=None,
        ),
    ] = None,
) -> str:
    """
    List repositories in a workspace/project or all accessible repositories.

    Args:
        ctx: The MCP context.
        workspace: Optional workspace name or project key to filter repositories.

    Returns:
        JSON string containing list of repositories with their details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        repositories = bitbucket.get_repositories(workspace)
        repositories = [
            r.model_dump(mode="json", serialize_as_any=True) for r in repositories
        ]
        return json.dumps(repositories, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = "An unexpected error occurred while fetching repositories."
            logger.exception("Unexpected error in bitbucket_list_repositories:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_repositories failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_repository_info(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
) -> str:
    """
    Get detailed information about a specific repository.

    Args:
        ctx: The MCP context.
        workspace: Workspace name or project key.
        repository: Repository name.

    Returns:
        JSON string containing repository details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        repo_info = bitbucket.get_repository_info(workspace, repository)
        return json.dumps(
            repo_info.model_dump(mode="json", serialize_as_any=True), indent=2
        )
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching repository info for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_get_repository_info:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_repository_info failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def list_branches(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    base: Annotated[
        str,
        Field(description="The base branch"),
    ] = None,
    branch_filter: Annotated[
        str,
        Field(description="Branch pattern to filter on."),
    ] = None,
    start: Annotated[
        int,
        Field(description="Starting index."),
    ] = 0,
    limit: Annotated[
        int,
        Field(description="Maximum number of branches to return"),
    ] = None,
) -> str:
    """
    List all branches in a repository.

    Args:
        ctx: The MCP context.
        workspace: Workspace name or project key.
        repository: Repository name.
        base: The base branch from which to find branches.
        branch_filter: Branch pattern to filter on.
        start: Starting index.
        limit: Maximum number of branches to fetch.

    Returns:
        JSON string containing list of branches with their details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        branches = bitbucket.get_branches(
            workspace, repository, base, branch_filter, start, limit
        )
        # Convert model objects to dictionaries for JSON serialization
        branch_dicts = [
            branch.model_dump(mode="json", serialize_as_any=True) for branch in branches
        ]
        return json.dumps(branch_dicts, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching branches for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_list_branches:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_branches failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_default_branch(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
) -> str:
    """
    Get the default branch for a repository.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.

    Returns:
        JSON string containing default branch information.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        default_branch = bitbucket.get_default_branch(workspace, repository)
        if default_branch:
            return json.dumps(
                default_branch.model_dump(mode="json", serialize_as_any=True), indent=2
            )
        else:
            return json.dumps({"error": "No default branch found"})
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching default branch for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_get_default_branch:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_default_branch failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_file_content(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    file_path: Annotated[
        str,
        Field(description="Path to the file in the repository"),
    ],
    branch: Annotated[
        str,
        Field(description="Branch name to read from"),
    ] = "main",
    sample: Annotated[
        int,
        Field(
            description="Read top N lines of a file. -1 for full file content.",
            default=-1,
        ),
    ] = -1,
) -> str:
    """
    Get the content of a specific file from a repository.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        file_path: Path to the file in the repository.
        branch: Branch name to read from (default: main).

    Returns:
        JSON string containing file content and metadata.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        content = bitbucket.get_file_content(workspace, repository, file_path, branch)
        content = content.decode("utf-8")
        if sample and sample > 0:
            content = "\n".join(content.splitlines()[:sample])
        return json.dumps(
            {
                "workspace": workspace,
                "repository": repository,
                "file_path": file_path,
                "branch": branch,
                "content": content,
            },
            indent=2,
        )
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching file content for {workspace}/{repository}/{file_path}."
            logger.exception("Unexpected error in bitbucket_get_file_content:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_file_content failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def list_directory(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    path: Annotated[
        str,
        Field(description="Directory path in the repository"),
    ] = "",
    branch: Annotated[
        str,
        Field(description="Branch name to list from"),
    ] = "main",
) -> str:
    """
    List the contents of a directory in a repository.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        path: Directory path in the repository (empty for root).
        branch: Branch name to list from (default: main).

    Returns:
        JSON string containing directory contents.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        contents = list(
            bitbucket.get_directory_content(workspace, repository, path, branch)
        )
        return json.dumps(contents, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while listing directory for {workspace}/{repository}/{path}."
            logger.exception("Unexpected error in bitbucket_list_directory:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_directory failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def search_code(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Search query string to match against code content"),
    ],
    start: Annotated[
        int,
        Field(description="Starting index for pagination", default=0, ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results per page",
            default=10,
            ge=1,
            le=100,
        ),
    ] = 10,
    branch: Annotated[
        str | None,
        Field(
            description="Optional branch name to search within (e.g., 'main', 'develop', 'feature/my-branch')",
            default=None,
        ),
    ] = None,
    repository: Annotated[
        str | None,
        Field(
            description="Optional repository slug to limit search scope",
            default=None,
        ),
    ] = None,
    project: Annotated[
        str | None,
        Field(
            description="Optional project key to limit search scope",
            default=None,
        ),
    ] = None,
) -> str:
    """
    Search for code across Bitbucket repositories with optional filtering.

    This tool searches code content across repositories using the Bitbucket
    Server/Data Center search API. Results include code snippets with matching
    lines highlighted. You can optionally filter by branch, repository, and/or project.

    When repository and/or project filters are specified, the tool automatically
    fetches additional pages (up to 10) to ensure you get the requested number
    of filtered results, since filtering happens client-side.

    Note:
        This feature is only available for Bitbucket Server/Data Center.
        It is NOT supported in Bitbucket Cloud.

    Args:
        ctx: The MCP context.
        query: Search query string to match against code content.
        start: Starting index for pagination (default: 0).
        limit: Maximum number of results per page (default: 10, max: 100).
        branch: Optional branch name to search within (e.g., 'main', 'develop').
        repository: Optional repository slug to limit search scope (auto-fetches pages).
        project: Optional project key to limit search scope (auto-fetches pages).

    Returns:
        JSON string containing search results with code snippets and pagination
        metadata.

    Raises:
        ValueError: If called on a Bitbucket Cloud instance.
        
    Examples:
        Search all repositories: search_code(query="def main")
        Search specific branch: search_code(query="def main", branch="develop")
        Search in specific repo: search_code(query="manifest", repository="taas-spydr", project="ASX-XENA")
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        
        # Auto-quote multi-word queries for phrase search
        # Skip if query already has quotes or appears to be using search operators
        processed_query = query
        if " " in query and not any(
            marker in query for marker in ['"', "AND", "OR", "NOT"]
        ):
            processed_query = f'"{query}"'
            logger.info(
                f"Auto-quoting multi-word query for phrase search: {processed_query}"
            )
        
        search_result = bitbucket.search_code(
            query=processed_query,
            start=start,
            limit=limit,
            branch=branch,
            repository=repository,
            project=project,
        )

        # Convert model to dictionary for JSON serialization
        result_dict = search_result.model_dump(mode="json", serialize_as_any=True)

        # If total count exceeds 10,000, provide summary instead of full details
        if search_result.total_count > 10000:
            # Create a summarized version with limited code snippets
            summarized_results = []
            for result in search_result.results:
                # Limit code snippets to first 2 per file
                limited_snippets = result.code_snippets[:2] if result.code_snippets else []
                # Limit lines in each snippet to first 5
                limited_snippets = [
                    snippet[:5] for snippet in limited_snippets
                ]

                summarized_result = {
                    "project_key": result.project_key,
                    "project_name": result.project_name,
                    "repository_name": result.repository_name,
                    "repository_slug": result.repository_slug,
                    "file_path": result.file_path,
                    "hit_count": result.hit_count,
                    "code_snippets": [[{"line_number": line.line_number, "text": line.text} for line in snippet] for snippet in limited_snippets],
                    "_note": "Code snippets limited due to large result set"
                }
                summarized_results.append(summarized_result)

            result_dict = {
                "total_count": search_result.total_count,
                "start": search_result.start,
                "next_start": search_result.next_start,
                "is_last_page": search_result.is_last_page,
                "results": summarized_results,
                "_warning": f"Large result set detected ({search_result.total_count} total matches). Showing first {len(search_result.results)} results with limited code snippets. Use pagination (start/limit) to retrieve more specific results."
            }

        # Add warning if repository/project filter was used but returned fewer results than requested
        if (repository or project) and len(search_result.results) < limit:
            if result_dict.get("_warning"):
                result_dict["_warning"] += f" | Filtered for repository='{repository}' project='{project}' but found only {len(search_result.results)} results out of {limit} requested. Results for this repository may be sparse in the overall result set."
            else:
                result_dict["_info"] = f"Filtered for repository='{repository}' project='{project}'. Found {len(search_result.results)} results out of {limit} requested."

        return json.dumps(result_dict, indent=2)
    except ValueError as val_err:
        # Handle the Cloud vs Server/DC validation error
        error_message = str(val_err)
        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.warning(f"bitbucket_search_code validation error: {error_message}")
        return json.dumps(error_result, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        else:
            error_message = (
                f"An unexpected error occurred while searching code for query: {query}"
            )
            logger.exception("Unexpected error in bitbucket_search_code:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_search_code failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def deep_search_code(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Search query string to match against code content"),
    ],
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository slug/name"),
    ],
    branch: Annotated[
        str | None,
        Field(
            description="Optional specific branch name to search in (e.g., 'develop', 'main')",
            default=None,
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results to return",
            default=10,
            ge=1,
            le=100,
        ),
    ] = 10,
    search_all_branches_on_miss: Annotated[
        bool,
        Field(
            description="If True and no results found in specified branch, search all branches",
            default=True,
        ),
    ] = True,
) -> str:
    """
    Deep search for code in a specific repository with automatic branch fallback.

    This tool performs an intelligent search:
    1. If branch is specified, searches in that branch first
    2. If no results found in specified branch (and search_all_branches_on_miss=True),
       automatically searches across all branches in the repository
    3. Returns results grouped by branch with metadata

    This is perfect when you want to find code but aren't sure which branch it's in,
    or when you want to see if code exists across multiple branches.

    Note:
        This feature is only available for Bitbucket Server/Data Center.
        It is NOT supported in Bitbucket Cloud.

    Args:
        ctx: The MCP context.
        query: Search query string to match against code content.
        workspace: Workspace name (Cloud) or project key (Server/DC).
        repository: Repository slug/name.
        branch: Optional specific branch name to search in.
        limit: Maximum number of results to return (default: 10).
        search_all_branches_on_miss: If True, search all branches if target branch has no results.

    Returns:
        JSON string with results grouped by branch, including:
        - query: Original search query
        - repository: Repository info
        - target_branch: Initially requested branch
        - searched_branches: List of branches that were searched
        - results_by_branch: Results organized by branch
        - total_results: Total number of matches
        - found_in_target_branch: Whether results were found in the target branch

    Examples:
        # Search in develop branch, fallback to all branches
        deep_search_code(query="customfield_10531", workspace="ITX-ALE", 
                        repository="xena-jira-ai", branch="develop")
        
        # Search only in specific branch (no fallback)
        deep_search_code(query="customfield", workspace="ITX-ALE",
                        repository="xena-jira-ai", branch="main", 
                        search_all_branches_on_miss=False)
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        
        # Auto-quote multi-word queries for phrase search
        # Skip if query already has quotes or appears to be using search operators
        processed_query = query
        if " " in query and not any(
            marker in query for marker in ['"', "AND", "OR", "NOT"]
        ):
            processed_query = f'"{query}"'
            logger.info(
                f"Auto-quoting multi-word query for phrase search: {processed_query}"
            )
        
        result = bitbucket.deep_search_code(
            query=processed_query,
            workspace=workspace,
            repository=repository,
            branch=branch,
            limit=limit,
            search_all_branches_on_miss=search_all_branches_on_miss,
        )

        return json.dumps(result, indent=2)
    except ValueError as val_err:
        error_message = str(val_err)
        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.warning(f"bitbucket_deep_search_code validation error: {error_message}")
        return json.dumps(error_result, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        else:
            error_message = (
                f"An unexpected error occurred during deep search for query: {query}"
            )
            logger.exception("Unexpected error in bitbucket_deep_search_code:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_deep_search_code failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def smart_search_code(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Search query string to match against code content"),
    ],
    workspace: Annotated[
        str | None,
        Field(
            description="Workspace name (Cloud) or project key (Server/DC). Required when using branch-specific search.",
            default=None,
        ),
    ] = None,
    repository: Annotated[
        str | None,
        Field(
            description="Repository slug/name. Required when using branch-specific search.",
            default=None,
        ),
    ] = None,
    branch: Annotated[
        str | None,
        Field(
            description="Optional branch name. When specified with workspace and repository, uses deep search with automatic fallback across all branches.",
            default=None,
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results to return",
            default=10,
            ge=1,
            le=100,
        ),
    ] = 10,
    start: Annotated[
        int,
        Field(description="Starting index for pagination (used only in normal search)", default=0, ge=0),
    ] = 0,
) -> str:
    """
    **DEFAULT CODE SEARCH TOOL** - Smart code search that automatically chooses the best search strategy.

    **Use this tool for ALL code search requests unless the user explicitly asks for page-based navigation.**

    This tool intelligently routes your search:
    - When branch + workspace + repository are provided → Uses deep search with automatic 
      fallback across all branches in that specific repository
    - Otherwise → Uses normal cross-repository search

    This is the primary code search tool. Use search_code_paginated ONLY when users explicitly
    request page-based navigation (e.g., "show me page 2", "next page", "page 3 of results").

    Note:
        This feature is only available for Bitbucket Server/Data Center.
        It is NOT supported in Bitbucket Cloud.

    Args:
        ctx: The MCP context.
        query: Search query string to match against code content.
        workspace: Workspace name or project key (required for branch-specific search).
        repository: Repository slug/name (required for branch-specific search).
        branch: Optional branch name. Triggers deep search when provided with workspace and repository.
        limit: Maximum number of results to return (default: 10, max: 100).
        start: Starting index for pagination (used only in normal search).

    Returns:
        JSON string with search results. Format varies based on search type used:
        - Deep search: Results grouped by branch with metadata
        - Normal search: Standard search results with pagination

    Examples:
        # Branch-specific search (uses deep search)
        smart_search_code(query="customfield", workspace="ITX-ALE", 
                         repository="xena-jira-ai", branch="develop")
        
        # Cross-repository search (uses normal search)
        smart_search_code(query="xena.dev", limit=30)
        
        # Repository-scoped search without branch (uses normal search)
        smart_search_code(query="manifest", repository="xena-jira-ai", 
                         workspace="ITX-ALE")
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        
        # Auto-quote multi-word queries for phrase search
        # Skip if query already has quotes or appears to be using search operators
        processed_query = query
        if " " in query and not any(
            marker in query for marker in ['"', "AND", "OR", "NOT"]
        ):
            processed_query = f'"{query}"'
            logger.info(
                f"Auto-quoting multi-word query for phrase search: {processed_query}"
            )
        
        # Decision logic: Use deep search if branch is specified with workspace and repository
        if branch and workspace and repository:
            logger.info(
                f"Using deep search for '{processed_query}' in {workspace}/{repository} "
                f"(branch: {branch})"
            )
            result = bitbucket.deep_search_code(
                query=processed_query,
                workspace=workspace,
                repository=repository,
                branch=branch,
                limit=limit,
                search_all_branches_on_miss=True,
            )
            return json.dumps(result, indent=2)
        else:
            # Use normal search
            logger.info(
                f"Using normal search for '{processed_query}' "
                f"(workspace: {workspace}, repository: {repository}, branch: {branch})"
            )
            search_result = bitbucket.search_code(
                query=processed_query,
                start=start,
                limit=limit,
                branch=branch,
                repository=repository,
                project=workspace,
            )
            
            # Convert model to dictionary for JSON serialization
            result_dict = search_result.model_dump(mode="json", serialize_as_any=True)
            
            # If total count exceeds 10,000, provide summary
            if search_result.total_count > 10000:
                summarized_results = []
                for result in search_result.results:
                    limited_snippets = result.code_snippets[:2] if result.code_snippets else []
                    limited_snippets = [snippet[:5] for snippet in limited_snippets]
                    
                    summarized_result = {
                        "project_key": result.project_key,
                        "project_name": result.project_name,
                        "repository_name": result.repository_name,
                        "repository_slug": result.repository_slug,
                        "file_path": result.file_path,
                        "hit_count": result.hit_count,
                        "code_snippets": [
                            [{"line_number": line.line_number, "text": line.text} for line in snippet]
                            for snippet in limited_snippets
                        ],
                        "_note": "Code snippets limited due to large result set"
                    }
                    summarized_results.append(summarized_result)
                
                result_dict["results"] = summarized_results
                result_dict["_info"] = (
                    f"Large result set ({search_result.total_count} total). "
                    "Code snippets have been summarized. Use more specific filters "
                    "or pagination to get detailed results."
                )
            
            return json.dumps(result_dict, indent=2)
            
    except ValueError as val_err:
        error_message = str(val_err)
        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.warning(f"smart_search_code validation error: {error_message}")
        return json.dumps(error_result, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        else:
            error_message = (
                f"An unexpected error occurred during search for query: {query}"
            )
            logger.exception("Unexpected error in smart_search_code:")
        
        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"smart_search_code failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def search_code_paginated(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Search query string to match against code content"),
    ],
    page: Annotated[
        int,
        Field(description="Page number (1-based)", default=1, ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Field(
            description="Results per page",
            default=10,
            ge=1,
            le=100,
        ),
    ] = 10,
    branch: Annotated[
        str | None,
        Field(
            description="Optional branch name to search within",
            default=None,
        ),
    ] = None,
    repository: Annotated[
        str | None,
        Field(
            description="Optional repository slug to limit search scope",
            default=None,
        ),
    ] = None,
    project: Annotated[
        str | None,
        Field(
            description="Optional project key to limit search scope",
            default=None,
        ),
    ] = None,
) -> str:
    """
    **ONLY USE WHEN USER EXPLICITLY REQUESTS PAGE-BASED NAVIGATION.**

    Search code with user-friendly page-based pagination. Use this tool ONLY when the user
    specifically asks for page navigation (e.g., "show page 2", "next page", "go to page 3").

    For all other code search requests, use smart_search_code instead.

    This tool makes it easy to navigate through search results using page numbers
    instead of managing start indices. Perfect for implementing "next page" / 
    "previous page" functionality.

    The response includes helpful pagination metadata:
    - Current page and total pages
    - has_next / has_previous flags
    - next_page / previous_page numbers

    Note:
        This feature is only available for Bitbucket Server/Data Center.
        It is NOT supported in Bitbucket Cloud.

    Args:
        ctx: The MCP context.
        query: Search query string to match against code content.
        page: Page number (1-based, default: 1).
        page_size: Results per page (default: 10, max: 100).
        branch: Optional branch name to search within.
        repository: Optional repository slug to limit search scope.
        project: Optional project key to limit search scope.

    Returns:
        JSON string containing:
        - query: Original search query
        - page: Current page number
        - page_size: Results per page
        - total_count: Total number of matches
        - total_pages: Total number of pages
        - has_next: Boolean indicating if there's a next page
        - has_previous: Boolean indicating if there's a previous page
        - next_page: Next page number (or null)
        - previous_page: Previous page number (or null)
        - results: List of search results for current page
        - filters: Applied filters

    Examples:
        # Get first page
        search_code_paginated(query="customfield", page=1)
        
        # Get next page
        search_code_paginated(query="customfield", page=2)
        
        # Get page 3 with 20 results per page, filtered by repository
        search_code_paginated(query="customfield", page=3, page_size=20,
                             repository="xena-jira-ai", project="ITX-ALE")
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        
        # Auto-quote multi-word queries for phrase search
        # Skip if query already has quotes or appears to be using search operators
        processed_query = query
        if " " in query and not any(
            marker in query for marker in ['"', "AND", "OR", "NOT"]
        ):
            processed_query = f'"{query}"'
            logger.info(
                f"Auto-quoting multi-word query for phrase search: {processed_query}"
            )
        
        result = bitbucket.search_code_paginated(
            query=processed_query,
            page=page,
            page_size=page_size,
            branch=branch,
            repository=repository,
            project=project,
        )

        return json.dumps(result, indent=2)
    except ValueError as val_err:
        error_message = str(val_err)
        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.warning(f"bitbucket_search_code_paginated validation error: {error_message}")
        return json.dumps(error_result, indent=2)
    except Exception as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        else:
            error_message = (
                f"An unexpected error occurred during paginated search for query: {query}"
            )
            logger.exception("Unexpected error in bitbucket_search_code_paginated:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_search_code_paginated failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def list_pull_requests(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    state: Annotated[
        str,
        Field(description="Pull request state: OPEN, MERGED, DECLINED"),
    ] = "OPEN",
) -> str:
    """
    List pull requests for a repository.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        state: Pull request state filter (OPEN, MERGED, DECLINED).

    Returns:
        JSON string containing list of pull requests.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        pull_requests = bitbucket.get_pull_requests(workspace, repository, state)
        pr_dicts = list(pull_requests)
        return json.dumps(pr_dicts, indent=2)
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching pull requests for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_list_pull_requests:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_pull_requests failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def pull_request_activities(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    pull_request_id: Annotated[
        int,
        Field(description="Pull request ID to get comments for."),
    ],
) -> str:
    """
    Get all activities on a pull request.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        pull_request_id: Pull request ID to get comments for.

    Returns:
        JSON string containing list of pull requests.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        pull_requests = bitbucket.get_pull_request_activities(
            workspace, repository, pull_request_id
        )
        return json.dumps(pull_requests, indent=2)
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching pull requests for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_list_pull_requests:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_list_pull_requests failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_pull_request(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    pull_request_id: Annotated[
        int,
        Field(description="Pull request ID"),
    ],
) -> str:
    """
    Get detailed information about a specific pull request.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        pull_request_id: Pull request ID.

    Returns:
        JSON string containing pull request details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        pull_request = bitbucket.get_pull_request(
            workspace, repository, pull_request_id
        )
        return json.dumps(
            pull_request.model_dump(mode="json", serialize_as_any=True), indent=2
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching pull request {pull_request_id} for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_get_pull_request:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_pull_request failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_commit_changes(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    commit_id: Annotated[
        str,
        Field(description="ID of the commit whose changes are being fetched."),
    ],
    merges: Annotated[
        Literal["include", "exclude", "only"],
        Field(
            description="Filter merges ('include', 'exclude', 'only') (default: include)"
        ),
    ] = "include",
    hash_newest: Annotated[
        str,
        Field(description="Fetch changes for a particular commit hash."),
    ] = None,
) -> str:
    """
    Get commit history for a repository branch.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        commit_id: ID of the commit whose changes are being fetched.
        merges: Filter merges ('include', 'exclude', 'only') (default: include)
        hash_newest: Fetch changes for a particular commit hash.

    Returns:
        JSON string containing commit history.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        commits = bitbucket.get_commit_changes(
            workspace, repository, commit_id, merges, hash_newest
        )
        return json.dumps(
            commits.model_dump(mode="json", serialize_as_any=True), indent=2
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching commits for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_get_commits:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_commits failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "read"})
async def get_commits(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    limit: Annotated[
        int,
        Field(description="Maximum number of commits to return"),
    ] = 25,
    until: Annotated[
        str,
        Field(
            description="The commit ID or ref (inclusively) to retrieve commits before"
        ),
    ] = None,
    since: Annotated[
        str,
        Field(
            description="The commit ID or ref (inclusively) to retrieve commits after"
        ),
    ] = None,
) -> str:
    """
    Get commit history for a repository branch.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        until: The commit ID or ref (inclusively) to retrieve commits before
        limit: Maximum number of commits to return (default: 25).
        since: The commit ID or ref (inclusively) to retrieve commits after

    Returns:
        JSON string containing commit history.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)
        commits = bitbucket.get_commits(
            workspace, repository, limit=limit, until=until, since=since
        )

        commit_dicts = [
            commit.model_dump(mode="json", serialize_as_any=True) for commit in commits
        ]
        return json.dumps(commit_dicts, indent=2)
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while fetching commits for {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_get_commits:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_get_commits failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "write"})
@check_write_access
async def create_pull_request(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    title: Annotated[
        str,
        Field(description="Pull request title"),
    ],
    source_branch: Annotated[
        str,
        Field(description="Source branch name"),
    ],
    destination_branch: Annotated[
        str,
        Field(description="Destination branch name"),
    ] = "main",
    description: Annotated[
        str | None,
        Field(description="Pull request description"),
    ] = None,
) -> str:
    """
    Create a new pull request.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        title: Pull request title.
        source_branch: Source branch name.
        destination_branch: Destination branch name (default: main).
        description: Optional pull request description.

    Returns:
        JSON string containing the created pull request details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)

        pr_data = {
            "title": title,
            "description": description,
            "state": "OPEN",
            "open": True,
            "closed": False,
            "fromRef": {
                "id": f"refs/heads/{source_branch}",
                "repository": {
                    "slug": repository,
                    "name": None,
                    "project": {"key": workspace},
                },
            },
            "toRef": {
                "id": f"refs/heads/{destination_branch}",
                "repository": {
                    "slug": repository,
                    "name": None,
                    "project": {"key": workspace},
                },
            },
            "locked": False,
            "reviewers": [],
        }

        result = bitbucket.create_pull_request(workspace, repository, pr_data)

        return json.dumps(
            {
                "success": True,
                "pull_request": result,
            },
            indent=2,
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while creating pull request in {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_create_pull_request:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_create_pull_request failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "write"})
@check_write_access
async def create_branch(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    branch_name: Annotated[
        str,
        Field(description="New branch name"),
    ],
    source_branch: Annotated[
        str,
        Field(description="Source branch to create from"),
    ] = "main",
) -> str:
    """
    Create a new branch in a repository.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        branch_name: New branch name.
        source_branch: Source branch to create from (default: main).

    Returns:
        JSON string containing the created branch details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)

        branch_data = {
            "name": branch_name,
            "target": {"branch": {"name": source_branch}},
        }

        result = bitbucket.create_branch(workspace, repository, branch_data)

        return json.dumps(
            {
                "success": True,
                "branch": result,
                "source_branch": source_branch,
            },
            indent=2,
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while creating branch {branch_name} in {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_create_branch:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"bitbucket_create_branch failed: {error_message}")
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "write"})
@check_write_access
async def add_pull_request_blocker_comment(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    pull_request_id: Annotated[
        int,
        Field(description="Pull request ID"),
    ],
    comment: Annotated[
        str,
        Field(description="Comment text"),
    ],
    severity: Annotated[
        Literal["NORMAL", "BLOCKER"],
        Field(description="Severity of the blocker."),
    ] = "NORMAL",
) -> str:
    """
    Add a comment to a pull request.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        pull_request_id: Pull request ID.
        comment: Comment text.
        severity: Severity of the blocker. (Normal or Blocker) (default: NORMAL)

    Returns:
        JSON string containing the created comment details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)

        result = bitbucket.add_pull_request_blocker_comment(
            workspace, repository, pull_request_id, comment, severity
        )

        return json.dumps(
            {
                "success": True,
                "comment": result,
                "pull_request_id": pull_request_id,
            },
            indent=2,
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while adding blocker comment to PR {pull_request_id} in {workspace}/{repository}."
            logger.exception(
                "Unexpected error in bitbucket_add_pull_request_blocker_comment:"
            )

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(
            log_level,
            f"bitbucket_add_pull_request_blocker_comment failed: {error_message}",
        )
        return json.dumps(error_result, indent=2)


@bitbucket_mcp.tool(tags={"bitbucket", "write"})
@check_write_access
async def add_pull_request_comment(
    ctx: Context,
    workspace: Annotated[
        str,
        Field(description="Workspace name (Cloud) or project key (Server/DC)"),
    ],
    repository: Annotated[
        str,
        Field(description="Repository name"),
    ],
    pull_request_id: Annotated[
        int,
        Field(description="Pull request ID"),
    ],
    comment: Annotated[
        str,
        Field(description="Comment text"),
    ],
) -> str:
    """
    Add a comment to a pull request.

    Args:
        workspace: Workspace name or project key.
        repository: Repository name.
        pull_request_id: Pull request ID.
        comment: Comment text.

    Returns:
        JSON string containing the created comment details.

    Raises:
        ValueError: If the Bitbucket client is not configured or available.
    """
    try:
        bitbucket = await get_bitbucket_fetcher(ctx)

        result = bitbucket.add_pull_request_comment(
            workspace, repository, pull_request_id, comment
        )

        return json.dumps(
            {
                "success": True,
                "comment": result,
                "pull_request_id": pull_request_id,
            },
            indent=2,
        )
    except Exception as e:
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"
        else:
            error_message = f"An unexpected error occurred while adding comment to PR {pull_request_id} in {workspace}/{repository}."
            logger.exception("Unexpected error in bitbucket_add_pull_request_comment:")

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(
            log_level, f"bitbucket_add_pull_request_comment failed: {error_message}"
        )
        return json.dumps(error_result, indent=2)

"""Module for Bitbucket code search operations."""

import logging
from typing import Any

from requests.exceptions import HTTPError, RequestException

from ..exceptions import MCPAtlassianAuthenticationError
from ..models.bitbucket.common import BitbucketCodeSearchResult
from .client import BitbucketClient

logger = logging.getLogger("mcp-bitbucket")


class SearchMixin(BitbucketClient):
    """Mixin for Bitbucket code search operations.

    This mixin provides methods for searching code across repositories in
    Bitbucket Server/Data Center using the REST API search endpoint.

    Note:
        Code search is only available for Bitbucket Server/Data Center,
        not for Bitbucket Cloud.
    """

    def search_code(
        self,
        query: str,
        start: int = 0,
        limit: int = 10,
        avatar_size: int = 64,
        branch: str | None = None,
        repository: str | None = None,
        project: str | None = None,
    ) -> BitbucketCodeSearchResult:
        """
        Search for code in Bitbucket repositories.

        This method searches code across all accessible repositories using the
        Bitbucket Server/Data Center search API. Results include code snippets
        with matching lines highlighted.

        When repository and/or project filters are specified, the method will
        automatically fetch additional pages (up to 10) to ensure you get the
        requested number of filtered results.

        Args:
            query: Search query string to match against code content
            start: Starting index for pagination (default: 0)
            limit: Maximum number of results per page (default: 10, max: 100)
            avatar_size: Avatar image size in pixels (default: 64)
            branch: Optional branch name to search within (e.g., 'main', 'develop')
            repository: Optional repository slug to limit search scope
                (auto-fetches pages)
            project: Optional project key to limit search scope
                (auto-fetches pages)

        Returns:
            BitbucketCodeSearchResult object containing search results and
            pagination metadata

        Raises:
            ValueError: If this method is called on a Bitbucket Cloud instance
            MCPAtlassianAuthenticationError: If authentication fails (401/403)
            Exception: If there is an error performing the search

        Note:
            This feature is only available for Bitbucket Server/Data Center.
            Bitbucket Cloud does not support code search via the REST API.
            Repository/project filtering happens client-side with automatic pagination.

        Examples:
            # Search all repositories
            results = client.search_code("def main")

            # Search in specific branch
            results = client.search_code("def main", branch="develop")

            # Search in specific repository (will fetch multiple pages if needed)
            results = client.search_code(
                "manifest",
                repository="taas-spydr",
                project="ASX-XENA"
            )
        """
        if self.config.is_cloud:
            error_msg = (
                "Code search is not available for Bitbucket Cloud. "
                "This feature is only supported in Bitbucket Server/Data Center."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Construct the search endpoint URL
            search_url = f"{self.config.url}/rest/search/latest/search"
            params = {"avatarSize": avatar_size}

            # Build the payload with proper start and limit parameters
            payload = {
                "query": query,
                "entities": {"code": {"start": start, "limit": limit}}
            }

            logger.info(
                f"Initiating code search request to Bitbucket API "
                f"with payload: {payload}"
            )

            logger.debug(
                f"Searching code with query: '{query}', "
                f"start: {start}, limit: {limit}, "
                f"branch: {branch}, repository: {repository}, project: {project}"
            )

            # Make the request using the existing session with auth
            response = self.bitbucket._session.post(
                search_url, json=payload, params=params, timeout=30
            )
            response.raise_for_status()

            # Parse the response
            raw_results = response.json()

            logger.info(f"Raw API response: {raw_results}")

            # Convert to model object
            search_result = BitbucketCodeSearchResult.from_api_response(raw_results)

            # Filter results client-side based on project and repository
            # If filtering and we don't have enough results, fetch more pages
            if project or repository:
                filtered_results = []
                current_start = start
                current_search_result = search_result
                # When filtering by repo/project, allow more pages since
                # results are sparse
                max_pages = 100  # Increased from 10 to handle sparse results
                pages_fetched = 1

                while len(filtered_results) < limit and pages_fetched <= max_pages:
                    # Filter current page results
                    for result in current_search_result.results:
                        # Check project filter
                        if project and result.project_key != project:
                            continue

                        # Check repository filter
                        if repository and result.repository_slug != repository:
                            continue

                        filtered_results.append(result)

                        # Stop if we have enough filtered results
                        if len(filtered_results) >= limit:
                            break

                    # If we have enough results or reached last page, stop
                    if (
                        len(filtered_results) >= limit
                        or current_search_result.is_last_page
                    ):
                        break

                    # Fetch next page if needed
                    if current_search_result.next_start is not None:
                        current_start = current_search_result.next_start
                        pages_fetched += 1

                        logger.debug(
                            f"Fetching additional page (page {pages_fetched}) "
                            f"to get more filtered results. Current filtered "
                            f"count: {len(filtered_results)}"
                        )

                        # Fetch next page
                        next_payload = {
                            "query": query,
                            "entities": {
                                "code": {"start": current_start, "limit": limit}
                            }
                        }
                        next_response = self.bitbucket._session.post(
                            search_url, json=next_payload, params=params, timeout=30
                        )
                        next_response.raise_for_status()
                        current_search_result = (
                            BitbucketCodeSearchResult.from_api_response(
                                next_response.json()
                            )
                        )
                    else:
                        break

                # Limit to requested number of results
                search_result.results = filtered_results[:limit]

                # Warn if we didn't get enough results after hitting page limit
                if len(filtered_results) < limit and pages_fetched >= max_pages:
                    logger.warning(
                        f"Reached page limit ({max_pages} pages) while "
                        f"filtering for repository='{repository}', "
                        f"project='{project}'. Only found "
                        f"{len(filtered_results)} matching results out of "
                        f"{limit} requested."
                    )

                logger.info(
                    f"Filtered {len(search_result.results)} results after applying "
                    f"project/repository filters (fetched {pages_fetched} page(s))"
                )

            logger.info(
                f"Code search completed: {search_result.total_count} total matches, "
                f"returned {len(search_result.results)} results"
            )

            return search_result

        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Bitbucket API "
                    f"({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during code search: {http_err}")
                raise
        except RequestException as req_err:
            error_msg = f"Network error during code search: {str(req_err)}"
            logger.error(error_msg)
            raise Exception(error_msg) from req_err
        except Exception as e:
            error_msg = f"Error searching code: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    def search_all_code_pages(
        self,
        query: str,
        limit: int = 10,
        max_results: int | None = None,
        branch: str | None = None,
        repository: str | None = None,
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search all pages and return all code search results.

        This method automatically handles pagination and retrieves all matching
        results across multiple pages.

        Args:
            query: Search query string to match against code content
            limit: Number of results per page (default: 10)
            max_results: Maximum total results to retrieve (None for unlimited)
            branch: Optional branch name to search within
            repository: Optional repository slug to limit search scope
            project: Optional project key to limit search scope

        Returns:
            List of all search result dictionaries from all pages

        Raises:
            ValueError: If this method is called on a Bitbucket Cloud instance
            MCPAtlassianAuthenticationError: If authentication fails (401/403)
            Exception: If there is an error performing the search
        """
        all_results = []
        start = 0
        is_last_page = False
        results_fetched = 0

        logger.info(f"Starting paginated code search for query: '{query}'")

        while not is_last_page:
            # Check if we've reached max_results limit
            if max_results and results_fetched >= max_results:
                logger.info(
                    f"Reached max_results limit of {max_results}, "
                    "stopping pagination"
                )
                break

            # Adjust limit for last page if needed
            page_limit = limit
            if max_results:
                remaining = max_results - results_fetched
                page_limit = min(limit, remaining)

            try:
                search_result = self.search_code(
                    query,
                    start=start,
                    limit=page_limit,
                    branch=branch,
                    repository=repository,
                    project=project,
                )

                # Add results from this page
                result_dicts = [
                    r.model_dump(mode="json", serialize_as_any=True)
                    for r in search_result.results
                ]
                all_results.extend(result_dicts)
                results_fetched += len(result_dicts)

                logger.debug(
                    f"Fetched page with {len(result_dicts)} results "
                    f"(total: {results_fetched})"
                )

                # Check if we're on the last page
                is_last_page = search_result.is_last_page

                # Update start position for next page
                if search_result.next_start is not None:
                    start = search_result.next_start
                else:
                    start += limit

            except Exception as e:
                logger.error(f"Error during paginated search: {str(e)}")
                break

        logger.info(
            f"Completed paginated code search: {results_fetched} total results"
        )
        return all_results

    def deep_search_code(
        self,
        query: str,
        workspace: str,
        repository: str,
        branch: str | None = None,
        limit: int = 10,
        search_all_branches_on_miss: bool = True,
    ) -> dict[str, Any]:
        """
        Deep search for code in a specific repository with branch fallback.

        This method performs an intelligent search:
        1. If branch is specified, searches in that branch first
        2. If no results found in specified branch (and
           search_all_branches_on_miss=True), automatically searches across
           all branches in the repository
        3. Returns results grouped by branch with metadata

        Args:
            query: Search query string to match against code content
            workspace: Workspace name (Cloud) or project key (Server/DC)
            repository: Repository slug/name
            branch: Optional specific branch name to search in
            limit: Maximum number of results to return (default: 10)
            search_all_branches_on_miss: If True and no results found in
                specified branch, search all branches (default: True)

        Returns:
            Dictionary containing:
            - 'query': Original search query
            - 'repository': Repository info
            - 'target_branch': Branch that was requested (if any)
            - 'searched_branches': List of branches that were searched
            - 'results_by_branch': Dictionary mapping branch names to results
            - 'total_results': Total number of results found
            - 'found_in_target_branch': Boolean indicating if results found
              in target branch

        Raises:
            ValueError: If this method is called on a Bitbucket Cloud instance
            MCPAtlassianAuthenticationError: If authentication fails (401/403)
            Exception: If there is an error performing the search

        Examples:
            # Search in specific branch
            results = client.deep_search_code(
                query="customfield",
                workspace="ITX-ALE",
                repository="xena-jira-ai",
                branch="develop"
            )

            # Search in repo, fallback to all branches if needed
            results = client.deep_search_code(
                query="customfield",
                workspace="ITX-ALE",
                repository="xena-jira-ai",
                branch="feature/new-feature",
                search_all_branches_on_miss=True
            )
        """
        response = {
            "query": query,
            "repository": {"workspace": workspace, "name": repository},
            "target_branch": branch,
            "searched_branches": [],
            "results_by_branch": {},
            "total_results": 0,
            "found_in_target_branch": False,
        }

        logger.info(
            f"Starting deep search for '{query}' in {workspace}/{repository}"
            + (f" (branch: {branch})" if branch else "")
        )

        # Step 1: Search in specific branch if provided
        if branch:
            logger.info(f"Searching in target branch: {branch}")
            try:
                search_result = self.search_code(
                    query=query,
                    branch=branch,
                    repository=repository,
                    project=workspace,
                    limit=limit,
                )

                if search_result.results:
                    response["searched_branches"].append(branch)
                    response["results_by_branch"][branch] = [
                        r.model_dump(mode="json", serialize_as_any=True)
                        for r in search_result.results
                    ]
                    response["total_results"] = len(search_result.results)
                    response["found_in_target_branch"] = True

                    logger.info(
                        f"Found {len(search_result.results)} results in "
                        f"branch '{branch}'"
                    )
                    return response
                else:
                    logger.info(f"No results found in branch '{branch}'")

            except Exception as e:
                logger.warning(f"Error searching in branch '{branch}': {str(e)}")

        # Step 2: If no results in target branch, search all branches
        if search_all_branches_on_miss or not branch:
            logger.info(
                f"Searching across all branches in {workspace}/{repository}"
            )

            try:
                # Get all branches
                branches = self.bitbucket.get_branches(workspace, repository)
                logger.info(f"Found {len(branches)} branches in repository")

                # Search across each branch
                branches_searched = 0
                for branch_obj in branches:
                    branch_name = (
                        branch_obj.get("displayId")
                        or branch_obj.get("id", "").replace("refs/heads/", "")
                    )

                    # Skip if already searched
                    if branch_name in response["searched_branches"]:
                        continue

                    try:
                        logger.debug(f"Searching in branch: {branch_name}")
                        search_result = self.search_code(
                            query=query,
                            branch=branch_name,
                            repository=repository,
                            project=workspace,
                            limit=limit,
                        )

                        if search_result.results:
                            response["searched_branches"].append(branch_name)
                            response["results_by_branch"][branch_name] = [
                                r.model_dump(mode="json", serialize_as_any=True)
                                for r in search_result.results
                            ]
                            response["total_results"] += len(search_result.results)

                            logger.info(
                                f"Found {len(search_result.results)} results "
                                f"in branch '{branch_name}'"
                            )

                        branches_searched += 1

                    except Exception as e:
                        logger.debug(
                            f"Error searching branch '{branch_name}': {str(e)}"
                        )
                        continue

                logger.info(
                    f"Searched {branches_searched} branches, "
                    f"found results in {len(response['results_by_branch'])} branches"
                )

            except Exception as e:
                error_msg = f"Error getting branches for deep search: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg) from e

        if response["total_results"] == 0:
            logger.warning(f"No results found in any branch for query '{query}'")

        return response

    def search_code_paginated(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10,
        branch: str | None = None,
        repository: str | None = None,
        project: str | None = None,
    ) -> dict[str, Any]:
        """
        Search code with user-friendly pagination (page numbers instead of start index).

        This is a convenience wrapper around search_code that uses page numbers
        (1-based) instead of start indices, making it easier to implement
        "next page" / "previous page" functionality.

        Args:
            query: Search query string to match against code content
            page: Page number (1-based, default: 1)
            page_size: Results per page (default: 10, max: 100)
            branch: Optional branch name to search within
            repository: Optional repository slug to limit search scope
            project: Optional project key to limit search scope

        Returns:
            Dictionary containing:
            - 'query': Original search query
            - 'page': Current page number
            - 'page_size': Results per page
            - 'total_count': Total number of matches
            - 'total_pages': Total number of pages
            - 'has_next': Boolean indicating if there's a next page
            - 'has_previous': Boolean indicating if there's a previous page
            - 'next_page': Next page number (or None)
            - 'previous_page': Previous page number (or None)
            - 'results': List of search results for current page
            - 'filters': Applied filters (branch, repository, project)

        Raises:
            ValueError: If page < 1 or page_size < 1 or page_size > 100
            MCPAtlassianAuthenticationError: If authentication fails (401/403)
            Exception: If there is an error performing the search

        Examples:
            # Get first page (10 results)
            page1 = client.search_code_paginated("customfield", page=1)

            # Get next page
            if page1['has_next']:
                page2 = client.search_code_paginated("customfield", page=2)

            # Get specific page with custom page size
            page3 = client.search_code_paginated("customfield", page=3, page_size=20)
        """
        # Validate inputs
        if page < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("Page size must be between 1 and 100")

        # Calculate start index (convert 1-based page to 0-based start)
        start = (page - 1) * page_size

        logger.info(
            f"Searching code (page {page}, size {page_size}): '{query}'"
        )

        # Perform search
        search_result = self.search_code(
            query=query,
            start=start,
            limit=page_size,
            branch=branch,
            repository=repository,
            project=project,
        )

        # Calculate pagination metadata
        total_count = search_result.total_count
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        has_next = page < total_pages
        has_previous = page > 1

        response = {
            "query": query,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
            "results": [
                r.model_dump(mode="json", serialize_as_any=True)
                for r in search_result.results
            ],
            "filters": {
                "branch": branch,
                "repository": repository,
                "project": project,
            },
        }

        logger.info(
            f"Page {page}/{total_pages}: {len(response['results'])} results "
            f"(total: {total_count})"
        )

        return response

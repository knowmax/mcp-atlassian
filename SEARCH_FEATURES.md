# Bitbucket Search Features

## Overview
Three powerful search tools are available to enhance code search capabilities in Bitbucket:

1. **Smart Search** (`smart_search_code`) - **DEFAULT** - Automatically chooses the best search strategy
2. **Deep Search** (`deep_search_code`) - Intelligent branch-aware searching with automatic fallback
3. **Paginated Search** (`search_code_paginated`) - **ONLY for explicit page navigation requests**

---

## 1. Smart Search (`smart_search_code`) ⭐ DEFAULT SEARCH TOOL

### What It Does
**This is the PRIMARY code search tool** - use this for ALL code search requests unless the user explicitly asks for page-based navigation.

Automatically selects the optimal search strategy based on your parameters:
- **Branch specified with workspace & repository** → Uses deep search with automatic fallback
- **No branch or missing workspace/repository** → Uses normal cross-repository search

This is the **easiest tool to use** - just provide what you know, and it handles the rest!

### When to Use
- ✅ **ALL code search requests** (unless user explicitly asks for page navigation)
- ✅ You want the system to automatically choose the best search approach
- ✅ You're not sure whether to use deep search or normal search
- ✅ You want a single tool that works for all scenarios

### Usage Examples

#### Example 1: Branch-specific search (automatically uses deep search)
```python
smart_search_code(
    query="customfield",
    workspace="ITX-ALE",
    repository="xena-jira-ai",
    branch="develop"
)
```

**What happens:** Uses deep search, searches in `develop` branch first, automatically falls back to all branches if needed.

#### Example 2: Cross-repository search (automatically uses normal search)
```python
smart_search_code(
    query="xena.dev",
    limit=30
)
```

**What happens:** Uses normal search across all repositories.

#### Example 3: Repository-scoped without branch (uses normal search)
```python
smart_search_code(
    query="manifest",
    repository="xena-jira-ai",
    workspace="ITX-ALE",
    limit=20
)
```

**What happens:** Uses normal search limited to the specified repository.

### Parameters
- `query` (required): Search string
- `workspace` (optional): Project key (e.g., "ITX-ALE")
- `repository` (optional): Repo name (e.g., "xena-jira-ai")
- `branch` (optional): Branch name - triggers deep search when combined with workspace & repository
- `limit` (optional): Max results (default: 10, max: 100)
- `start` (optional): Starting index for pagination in normal search (default: 0)

---

## 2. Deep Search (`deep_search_code`)

### What It Does
Intelligently searches for code in a repository:
- Searches in a specific branch first (if provided)
- **Automatically falls back** to searching ALL branches if nothing found
- Returns results **grouped by branch**

### When to Use
- ✅ You want to find code but aren't sure which branch it's in
- ✅ You want to see if code exists across multiple branches
- ✅ You're searching for configuration that might vary by branch

### Usage Examples

#### Example 1: Search with automatic fallback
```python
# Search in develop branch, fallback to all branches if not found
deep_search_code(
    query="customfield_10531",
    workspace="ITX-ALE",
    repository="xena-jira-ai",
    branch="develop",
    search_all_branches_on_miss=True  # Default
)
```

**Response:**
```json
{
  "query": "customfield_10531",
  "repository": {
    "workspace": "ITX-ALE",
    "name": "xena-jira-ai"
  },
  "target_branch": "develop",
  "searched_branches": ["develop"],
  "results_by_branch": {
    "develop": [
      {
        "file_path": "manifest.yaml",
        "line_number": 60,
        "code_snippet": "acceptanceCriteria: customfield_10531"
      }
    ]
  },
  "total_results": 1,
  "found_in_target_branch": true
}
```

#### Example 2: Search only specific branch (no fallback)
```python
deep_search_code(
    query="customfield",
    workspace="ITX-ALE",
    repository="xena-jira-ai",
    branch="main",
    search_all_branches_on_miss=False  # Disable fallback
)
```

#### Example 3: Search all branches from the start
```python
deep_search_code(
    query="xena.dev",
    workspace="ITX-ALE",
    repository="xena-jira-ai",
    branch=None,  # No specific branch
    limit=20
)
```

**Response shows results from all branches:**
```json
{
  "query": "xena.dev",
  "repository": {...},
  "target_branch": null,
  "searched_branches": ["main", "develop", "feature/AFIG-11112"],
  "results_by_branch": {
    "main": [...],
    "develop": [...],
    "feature/AFIG-11112": [...]
  },
  "total_results": 15,
  "found_in_target_branch": false
}
```

### Parameters
- `query` (required): Search string
- `workspace` (required): Project key (e.g., "ITX-ALE")
- `repository` (required): Repo name (e.g., "xena-jira-ai")
- `branch` (optional): Specific branch to search first
- `limit` (optional): Max results per branch (default: 10)
- `search_all_branches_on_miss` (optional): Fallback flag (default: True)

---

## 3. Paginated Search (`search_code_paginated`) 

### ⚠️ ONLY USE WHEN USER EXPLICITLY REQUESTS PAGE-BASED NAVIGATION

### What It Does
Makes pagination simple with **page numbers** instead of managing start indices:
- Uses familiar page numbers (1, 2, 3...)
- Provides helpful navigation metadata
- Shows total pages and has_next/has_previous flags

**IMPORTANT:** This tool should ONLY be used when the user explicitly asks for page navigation 
like "show page 2", "next page", "go to page 3", etc. For all other code searches, use 
`smart_search_code` instead.

### When to Use
- ✅ **ONLY when user explicitly asks for page navigation** ("page 2", "next page", etc.)
- ✅ You need to browse through many search results with page numbers
- ✅ You want "next 10" / "previous 10" functionality
- ✅ You're building a UI or iterative search workflow

### When NOT to Use
- ❌ General code search requests (use `smart_search_code` instead)
- ❌ User doesn't mention pages or pagination
- ❌ First-time search requests

### Usage Examples

#### Example 1: Get first page
```python
search_code_paginated(
    query="customfield",
    page=1,
    page_size=10
)
```

**Response:**
```json
{
  "query": "customfield",
  "page": 1,
  "page_size": 10,
  "total_count": 417,
  "total_pages": 42,
  "has_next": true,
  "has_previous": false,
  "next_page": 2,
  "previous_page": null,
  "results": [...10 results...],
  "filters": {
    "branch": null,
    "repository": null,
    "project": null
  }
}
```

#### Example 2: Navigate to next page
```python
# Get page 2
search_code_paginated(
    query="customfield",
    page=2,
    page_size=10
)
```

#### Example 3: Larger page with filters
```python
# Get page 3 with 20 results, filtered by repo
search_code_paginated(
    query="customfield",
    page=3,
    page_size=20,
    repository="xena-jira-ai",
    project="ITX-ALE"
)
```

**Response:**
```json
{
  "query": "customfield",
  "page": 3,
  "page_size": 20,
  "total_count": 100,
  "total_pages": 5,
  "has_next": true,
  "has_previous": true,
  "next_page": 4,
  "previous_page": 2,
  "results": [...20 results...],
  "filters": {
    "branch": null,
    "repository": "xena-jira-ai",
    "project": "ITX-ALE"
  }
}
```

### Parameters
- `query` (required): Search string
- `page` (optional): Page number, 1-based (default: 1)
- `page_size` (optional): Results per page (default: 10, max: 100)
- `branch` (optional): Filter by branch
- `repository` (optional): Filter by repository
- `project` (optional): Filter by project

### Pagination Workflow
```python
# Start at page 1
page1 = search_code_paginated(query="function", page=1)

# Check if more pages exist
if page1['has_next']:
    # Get next page
    page2 = search_code_paginated(query="function", page=2)
    
    if page2['has_next']:
        page3 = search_code_paginated(query="function", page=3)

# Or go back
if page3['has_previous']:
    page2_again = search_code_paginated(query="function", page=2)
```

---

## Comparison: When to Use Which?

| Feature | `smart_search_code` ⭐ DEFAULT | `search_code` | `search_code_paginated` | `deep_search_code` |
|---------|-------------------------------|---------------|-------------------------|-------------------|
| **Best For** | **ALL general searches** | Quick searches | **ONLY page navigation** | Finding across branches |
| **Pagination** | Auto (based on mode) | Manual (start index) | User-friendly (page #) | N/A |
| **Branch Aware** | ✅ Auto deep search | Filter only | Filter only | ✅ Smart fallback |
| **Results Format** | Auto (based on mode) | Flat list | Flat list | Grouped by branch |
| **Use Case** | **Default for all searches** | Single query | Explicit page requests | Branch uncertainty |
| **Auto-routing** | ✅ Yes | No | No | No |

### Quick Decision Guide

**Use `smart_search_code` when:** ⭐ **DEFAULT CHOICE**
- **ALL code search requests** (unless user explicitly asks for page navigation)
- You want the system to choose the best approach
- You're searching with a branch in a specific repo
- You're doing a general cross-repo search

**Use `search_code_paginated` when:** ⚠️ **EXPLICIT PAGINATION ONLY**
- **User explicitly asks for page navigation** ("show page 2", "next page", etc.)
- You're building a UI with pagination
- You want easy "next/previous" navigation
- You need pagination metadata

**Use `deep_search_code` when:**
- You explicitly want branch-grouped results
- You need control over the fallback behavior
- You're comparing code across branches

**Use `search_code` when:**
- You need low-level control
- You're integrating with existing code
- You're building custom pagination logic

---

## Migration Guide

### Before (old way)
```python
# Page 1
search_code(query="test", start=0, limit=10)

# Page 2  
search_code(query="test", start=10, limit=10)

# Page 3
search_code(query="test", start=20, limit=10)
```

### After (new way)
```python
# Page 1
search_code_paginated(query="test", page=1)

# Page 2
search_code_paginated(query="test", page=2)

# Page 3
search_code_paginated(query="test", page=3)
```

Much cleaner! 🎉

---

## Notes

- ✅ All tools are **Bitbucket Server/Data Center only** (not Cloud)
- ✅ `smart_search_code` is the **DEFAULT tool for ALL code searches**
- ⚠️ Use `search_code_paginated` **ONLY when user explicitly requests page navigation**
- ✅ Smart search automatically routes to deep search when branch is specified with workspace & repository
- ✅ Deep search may be slower for repos with many branches
- ✅ Pagination metadata helps you build better UIs
- ✅ All existing `search_code` functionality still works
- ✅ Deep search is kept as **separate code** for explicit control and testability

## Testing

To test the new features, run:
```bash
uv run mcp-atlassian
```

Then use the MCP tools through your client!

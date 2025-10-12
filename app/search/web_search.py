import os
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup


async def web_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    engine = os.getenv("SEARCH_ENGINE", "ddg").lower()
    if engine == "none":
        return []
    
    # 자동차 SW 특화 검색 엔진 선택
    if engine in ("ddg", "duckduckgo"):
        return await _search_duckduckgo(query, top_k)
    elif engine == "google":
        return await _search_google(query, top_k)
    elif engine == "bing":
        return await _search_bing(query, top_k)
    elif engine == "stackoverflow":
        return await _search_stackoverflow(query, top_k)
    elif engine == "github":
        return await _search_github(query, top_k)
    elif engine == "official_docs":
        return await _search_official_docs(query, top_k)
    else:
        # 기본값으로 DuckDuckGo 사용
        return await _search_duckduckgo(query, top_k)


async def _search_duckduckgo(query: str, top_k: int) -> List[Dict[str, Any]]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[Dict[str, Any]] = []
        for a in soup.select(".result__a")[: top_k * 2]:
            title = a.get_text(strip=True)
            href = a.get("href")
            snippet_el = a.find_parent(".result__title").find_next_sibling(".result__snippet")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            if title and href:
                results.append({"title": title, "url": href, "snippet": snippet})
            if len(results) >= top_k:
                break
        return results


async def _search_google(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Google 검색 (자동차 SW 관련 결과 우선)"""
    url = "https://www.google.com/search"
    params = {
        "q": f"{query} automotive software tasking nxp polyspace",
        "num": top_k
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[Dict[str, Any]] = []
            
            for result in soup.select("h3")[:top_k]:
                title = result.get_text(strip=True)
                link_el = result.find_parent("a")
                if link_el:
                    href = link_el.get("href")
                    snippet_el = link_el.find_next_sibling()
                    snippet = snippet_el.get_text(" ", strip=True)[:200] if snippet_el else ""
                    if title and href:
                        results.append({"title": title, "url": href, "snippet": snippet})
            
            return results
    except Exception as e:
        print(f"Google 검색 오류: {e}")
        return []


async def _search_bing(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Bing 검색"""
    url = "https://www.bing.com/search"
    params = {"q": f"{query} automotive embedded software"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[Dict[str, Any]] = []
            
            for result in soup.select(".b_title")[:top_k]:
                title = result.get_text(strip=True)
                link_el = result.find("a")
                if link_el:
                    href = link_el.get("href")
                    snippet_el = result.find_next_sibling()
                    snippet = snippet_el.get_text(" ", strip=True)[:200] if snippet_el else ""
                    if title and href:
                        results.append({"title": title, "url": href, "snippet": snippet})
            
            return results
    except Exception as e:
        print(f"Bing 검색 오류: {e}")
        return []


async def _search_stackoverflow(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Stack Overflow 검색 (자동차 SW 관련)"""
    url = "https://stackoverflow.com/search"
    params = {
        "q": f"{query} automotive embedded",
        "tab": "relevance"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[Dict[str, Any]] = []
            
            for result in soup.select(".s-post-summary")[:top_k]:
                title_el = result.select_one(".s-post-summary--title a")
                if title_el:
                    title = title_el.get_text(strip=True)
                    href = "https://stackoverflow.com" + title_el.get("href", "")
                    snippet_el = result.select_one(".s-post-summary--content-excerpt")
                    snippet = snippet_el.get_text(" ", strip=True)[:200] if snippet_el else ""
                    if title and href:
                        results.append({"title": title, "url": href, "snippet": snippet})
            
            return results
    except Exception as e:
        print(f"Stack Overflow 검색 오류: {e}")
        return []


async def _search_github(query: str, top_k: int) -> List[Dict[str, Any]]:
    """GitHub 검색 (자동차 SW 관련 프로젝트)"""
    url = "https://github.com/search"
    params = {
        "q": f"{query} automotive embedded",
        "type": "repositories"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[Dict[str, Any]] = []
            
            for result in soup.select(".repo-list-item")[:top_k]:
                title_el = result.select_one(".f4 a")
                if title_el:
                    title = title_el.get_text(strip=True)
                    href = "https://github.com" + title_el.get("href", "")
                    snippet_el = result.select_one(".mb-1")
                    snippet = snippet_el.get_text(" ", strip=True)[:200] if snippet_el else ""
                    if title and href:
                        results.append({"title": title, "url": href, "snippet": snippet})
            
            return results
    except Exception as e:
        print(f"GitHub 검색 오류: {e}")
        return []


async def _search_official_docs(query: str, top_k: int) -> List[Dict[str, Any]]:
    """공식 문서 사이트 검색 (자동차 SW 도구별)"""
    # 자동차 SW 도구별 공식 문서 사이트
    official_sites = [
        "infineon.com", "nxp.com", "mathworks.com", "vector.com", 
        "tasking.com", "polyspace.com", "arm.com", "autosar.org"
    ]
    
    results: List[Dict[str, Any]] = []
    
    for site in official_sites[:2]:  # 상위 2개 사이트만 검색
        url = f"https://www.google.com/search"
        params = {
            "q": f"site:{site} {query}",
            "num": 3
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                for result in soup.select("h3")[:3]:
                    title = result.get_text(strip=True)
                    link_el = result.find_parent("a")
                    if link_el:
                        href = link_el.get("href")
                        if href and site in href:
                            snippet_el = link_el.find_next_sibling()
                            snippet = snippet_el.get_text(" ", strip=True)[:200] if snippet_el else ""
                            results.append({"title": title, "url": href, "snippet": snippet})
                            
        except Exception as e:
            print(f"{site} 공식 문서 검색 오류: {e}")
            continue
    
    return results[:top_k]



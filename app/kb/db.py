import json
import os
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    summary = Column(String(4000), nullable=False)
    fix = Column(String(4000), nullable=False)
    tags = Column(String(512), nullable=True)


DB_PATH = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "kb.sqlite")
SEED_JSON = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "seed_kb.json")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_initialized() -> None:
    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        has_any = session.query(Article).first() is not None
        if not has_any and os.path.exists(SEED_JSON):
            with open(SEED_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                article = Article(
                    title=item.get("title", "Untitled"),
                    summary=item.get("summary", ""),
                    fix=item.get("fix", ""),
                    tags=",".join(item.get("tags", [])),
                )
                session.add(article)
            session.commit()
    finally:
        session.close()


def get_all_documents() -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        docs = session.query(Article).all()
        return [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "fix": a.fix,
                "tags": a.tags or "",
            }
            for a in docs
        ]
    finally:
        session.close()


def search_kb(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    KB 검색 (TF-IDF 또는 간단한 키워드 매칭)
    """
    docs = get_all_documents()
    if not docs:
        return []
    
    try:
        # TF-IDF 사용 (scikit-learn 있을 때)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel

        corpus = [f"{d['title']}\n{d['summary']}\n{d['fix']}\n{d['tags']}" for d in docs]
        vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)

        q_vec = vectorizer.transform([query])
        scores = linear_kernel(q_vec, tfidf_matrix).flatten()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        results: List[Dict[str, Any]] = []
        for idx, score in ranked:
            d = docs[idx]
            d_copy = dict(d)
            d_copy["score"] = float(score)
            results.append(d_copy)
        return results
    
    except ImportError:
        # scikit-learn 없으면 간단한 키워드 매칭으로 대체
        return _simple_keyword_search(docs, query, top_k)


def _simple_keyword_search(docs: List[Dict], query: str, top_k: int) -> List[Dict[str, Any]]:
    """간단한 키워드 매칭 검색 (scikit-learn 없이)"""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    results = []
    for doc in docs:
        # 각 문서의 모든 텍스트
        doc_text = f"{doc['title']} {doc['summary']} {doc['fix']} {doc['tags']}".lower()
        doc_words = set(doc_text.split())
        
        # 공통 단어 개수로 점수 계산
        common_words = query_words & doc_words
        score = len(common_words) / max(len(query_words), 1)
        
        # 제목에 포함되면 보너스
        if any(word in doc['title'].lower() for word in query_words):
            score += 0.3
        
        doc_copy = dict(doc)
        doc_copy["score"] = min(score, 1.0)
        results.append(doc_copy)
    
    # 점수순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def add_to_kb(
    title: str,
    summary: str,
    fix: str,
    tags: List[str],
    auto_approve: bool = False
) -> Dict[str, Any]:
    """
    KB에 새로운 지식 추가
    
    Args:
        title: 오류 제목
        summary: 오류 요약
        fix: 해결 방법
        tags: 태그 리스트
        auto_approve: 자동 승인 여부 (False면 수동 승인 필요)
    
    Returns:
        Dict: 추가된 항목 정보
    """
    session = SessionLocal()
    try:
        # 중복 체크
        existing = session.query(Article).filter(Article.title == title).first()
        if existing:
            return {
                "status": "duplicate",
                "message": f"이미 존재하는 제목: {title}",
                "id": existing.id
            }
        
        # 새 항목 추가
        article = Article(
            title=title,
            summary=summary,
            fix=fix,
            tags=",".join(tags)
        )
        session.add(article)
        session.commit()
        
        return {
            "status": "success",
            "message": f"KB에 추가 완료: {title}",
            "id": article.id,
            "auto_approved": auto_approve
        }
    except Exception as e:
        session.rollback()
        return {
            "status": "error",
            "message": f"KB 추가 실패: {str(e)}"
        }
    finally:
        session.close()


def update_kb(
    kb_id: int,
    title: str = None,
    summary: str = None,
    fix: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """
    KB 항목 업데이트
    
    Args:
        kb_id: 업데이트할 항목 ID
        title: 새 제목 (선택)
        summary: 새 요약 (선택)
        fix: 새 해결 방법 (선택)
        tags: 새 태그 (선택)
    
    Returns:
        Dict: 업데이트 결과
    """
    session = SessionLocal()
    try:
        article = session.query(Article).filter(Article.id == kb_id).first()
        if not article:
            return {
                "status": "not_found",
                "message": f"ID {kb_id}를 찾을 수 없습니다."
            }
        
        if title is not None:
            article.title = title
        if summary is not None:
            article.summary = summary
        if fix is not None:
            article.fix = fix
        if tags is not None:
            article.tags = ",".join(tags)
        
        session.commit()
        
        return {
            "status": "success",
            "message": f"KB 항목 {kb_id} 업데이트 완료",
            "id": kb_id
        }
    except Exception as e:
        session.rollback()
        return {
            "status": "error",
            "message": f"업데이트 실패: {str(e)}"
        }
    finally:
        session.close()


def delete_from_kb(kb_id: int) -> Dict[str, Any]:
    """
    KB에서 항목 삭제
    
    Args:
        kb_id: 삭제할 항목 ID
    
    Returns:
        Dict: 삭제 결과
    """
    session = SessionLocal()
    try:
        article = session.query(Article).filter(Article.id == kb_id).first()
        if not article:
            return {
                "status": "not_found",
                "message": f"ID {kb_id}를 찾을 수 없습니다."
            }
        
        title = article.title
        session.delete(article)
        session.commit()
        
        return {
            "status": "success",
            "message": f"KB 항목 삭제 완료: {title}",
            "id": kb_id
        }
    except Exception as e:
        session.rollback()
        return {
            "status": "error",
            "message": f"삭제 실패: {str(e)}"
        }
    finally:
        session.close()


def export_kb_to_json(output_path: str = None) -> str:
    """
    KB를 JSON 파일로 내보내기
    
    Args:
        output_path: 출력 파일 경로 (기본값: data/kb_export.json)
    
    Returns:
        str: 생성된 파일 경로
    """
    if output_path is None:
        output_path = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "kb_export.json")
    
    docs = get_all_documents()
    export_data = []
    
    for doc in docs:
        export_data.append({
            "title": doc["title"],
            "summary": doc["summary"],
            "fix": doc["fix"],
            "tags": doc["tags"].split(",") if doc["tags"] else []
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return output_path



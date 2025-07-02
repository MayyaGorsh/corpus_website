import ftplib
import os
from db import query_db
import re
from datetime import datetime

# FTP настройки
FTP_HOST = ""
FTP_USER = ''
FTP_PASS = ''

ICON_MAPPING = {
    ".doc": "doc-icon.png",
    ".docx": "doc-icon.png",
    ".rtf": "rtf-icon.png",
    ".pdf": "pdf-icon.png",
    ".xls": "xls-icon.png",
    ".xlsx": "xls-icon.png"
}


def get_all_collections():
    query = """
        SELECT *
        FROM COURT_collections
        ORDER BY id_collection
    """
    return query_db(query)


def get_collection_by_id(id_collection: int):
    query = """
        SELECT *
        FROM COURT_collections
        WHERE id_collection = %s
    """
    result = query_db(query, (id_collection,))
    return result[0] if result else None


def get_documents_from_ftp(ftp_path: str):
    print("📁 Получаем документы из FTP-пути:", ftp_path)
    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(ftp_path)
        files = ftp.nlst()
        print("🔹 Найдено файлов:", len(files))
        ftp.quit()
    except Exception as e:
        print(f"FTP error: {e}")
        return []

    result = []
    for filename in files:
        ext = os.path.splitext(filename)[1].lower()
        result.append({
            "filename": filename,
            "icon": ICON_MAPPING.get(ext, "file-icon.png"),
            "ftp_path": os.path.join(ftp_path, filename).replace("\\", "/")
        })

    result.sort(key=combined_sort_key)
    return result


def extract_year_from_filename(filename):
    match = re.search(r"\b(19|20)\d{2}\b", filename)
    return match.group(0) if match else ""


def get_documents_with_year_filter(id_collection: int, ftp_path: str, year_from: str = "", year_to: str = ""):
    query = """
        SELECT filename
        FROM COURT_documents
        WHERE id_collection = %s
    """
    rows = query_db(query, (id_collection,))

    for row in rows:
        fname = row["filename"]
        year = extract_year_from_filename(fname)
        row["year"] = year
        row["icon"] = ICON_MAPPING.get(os.path.splitext(fname)[1].lower(), "file-icon.png")
        row["ftp_path"] = f"{ftp_path}/{fname}".replace("\\", "/")

    # Получаем список годов
    years = sorted(set(r["year"] for r in rows if r["year"].isdigit()))

    # Фильтрация
    if year_from.isdigit() or year_to.isdigit():
        documents_filtered = []
        for r in rows:
            y = r["year"]
            if not y.isdigit():
                continue
            y = int(y)
            if (not year_from or y >= int(year_from)) and (not year_to or y <= int(year_to)):
                documents_filtered.append(r)
        rows = documents_filtered

    rows.sort(key=combined_sort_key)
    return rows, years


def extract_date(filename):
    """
    Ищет дату в формате дд.мм.гггг и возвращает datetime-объект для сортировки.
    Если не найдено — возвращает "далёкое прошлое" для безопасной сортировки.
    """
    match = re.search(r"\b(\d{2})[.\-](\d{2})[.\-](\d{4})\b", filename)
    if match:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return datetime(1900, 1, 1)  # fallback if дата неправильная
    return datetime(1900, 1, 1)


def combined_sort_key(doc):
    name = doc["filename"].lower()
    metrics_first = 0 if "all" in name and "metric" in name else 1
    date = extract_date(doc["filename"])
    return (metrics_first, date)

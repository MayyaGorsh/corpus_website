import os

from flask import (
    Flask,
    render_template,
    request,
    abort,
    send_file
)
from flask_restful import Api

from nominations_db_utils import (
    get_all_nominations,
    get_nomination_full
)
from court_db_utils import (
    get_collection_by_id,
    get_documents_from_ftp,
    get_documents_with_year_filter
)


app = Flask(__name__)
api = Api(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/nominations_corpus")
def nominations_corpus():
    query = request.args.get('query', '')
    nominations = get_all_nominations(query=query if query else None)
    return render_template("nominations_corpus.html", query=query, nominations=nominations)


@app.route("/nominations_corpus/<int:nomination_id>")
def nominations_detail(nomination_id):
    data = get_nomination_full(nomination_id)
    if not data:
        abort(404)
    return render_template("nominations_detail.html", nomination=data)


@app.route("/court_decisions_corpus")
def court_decisions_corpus():
    collection_43 = get_collection_by_id(43)
    ftp_path_43 = collection_43["path_to_folder"]
    documents_43, _ = get_documents_with_year_filter(43, ftp_path_43)

    return render_template(
        "court_decisions_corpus.html",
        documents_43=documents_43,
        collection_43=collection_43
    )


@app.route("/court_decisions_corpus/<int:id_collection>")
def court_collection_detail(id_collection):
    collection = get_collection_by_id(id_collection)
    if not collection:
        abort(404)

    ftp_path = collection["path_to_folder"]

    # для первой коллекции
    if id_collection == 42:
        year_from = request.args.get("year_from", "")
        year_to = request.args.get("year_to", "")
        documents, all_years = get_documents_with_year_filter(42, ftp_path, year_from, year_to)
    else:
        documents = get_documents_from_ftp(ftp_path)

    page = int(request.args.get("page", 1))
    page_size = 30

    total = len(documents)
    start = (page - 1) * page_size
    end = start + page_size
    documents = documents[start:end]

    total_pages = (total + page_size - 1) // page_size
    start = max(page - 2, 1)
    end = min(page + 2, total_pages)

    if id_collection == 42:
        return render_template(
            "court_corpus_collection.html",
            collection=collection,
            documents=documents,
            current_page=page,
            total_pages=total_pages,
            pagination_start=start,
            pagination_end=end,
            years=all_years,
            year_from=year_from,
            year_to=year_to
        )
    else:
        return render_template(
            "court_corpus_collection.html",
            collection=collection,
            documents=documents,
            current_page=page,
            total_pages=total_pages,
            pagination_start=start,
            pagination_end=end
        )


# FTP настройки
FTP_HOST = ""
FTP_USER = ""
FTP_PASS = ""


@app.route("/view")
def view_document():
    # done for court corpus
    ftp_path = request.args.get("path_to_folder")
    if not ftp_path:
        abort(400)

    filename = os.path.basename(ftp_path)

    try:
        import ftplib, tempfile
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            ftp.retrbinary(f"RETR {ftp_path}", tmp.write)
            tmp.flush()
            ftp.quit()
            return send_file(tmp.name, as_attachment=False, download_name=filename)
    except Exception as e:
        print(f"FTP view error: {e}")
        abort(500)


@app.route("/download")
def download_document():
    # done for court corpus
    ftp_path = request.args.get("path_to_folder")
    if not ftp_path:
        abort(400)

    filename = os.path.basename(ftp_path)

    try:
        import ftplib, tempfile
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            ftp.retrbinary(f"RETR {ftp_path}", tmp.write)
            tmp.flush()
            ftp.quit()
            return send_file(tmp.name, as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"FTP download error: {e}")
        abort(500)


@app.route("/download_archive/<int:id_collection>")
def download_archive(id_collection):
    # done for court corpus
    collection = get_collection_by_id(id_collection)
    if not collection:
        abort(404)

    import tempfile
    import zipfile
    from io import BytesIO
    import ftplib

    ftp_path = collection["path_to_folder"]
    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(ftp_path)
        files = ftp.nlst()

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zipf:
            for f in files:
                with tempfile.NamedTemporaryFile() as tmp:
                    ftp.retrbinary(f"RETR {f}", tmp.write)
                    tmp.flush()
                    tmp.seek(0)
                    zipf.writestr(f, tmp.read())

        ftp.quit()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/zip', as_attachment=True, download_name=f"{collection['title']}.zip")

    except Exception as e:
        print(f"FTP archive error: {e}")
        abort(500)


@app.route("/download_filtered_archive/<int:id_collection>")
def download_filtered_archive(id_collection):
    # done for court corpus, the 1st collection
    year_from = request.args.get("year_from", "")
    year_to = request.args.get("year_to", "")

    collection = get_collection_by_id(id_collection)
    if not collection:
        abort(404)

    if id_collection != 42:
        abort(400)

    ftp_path = collection["path_to_folder"]
    documents, _ = get_documents_with_year_filter(42, ftp_path, year_from, year_to)

    import tempfile, zipfile, ftplib
    from io import BytesIO

    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zipf:
            for doc in documents:
                ftp_path_full = doc['ftp_path']
                filename = os.path.basename(ftp_path_full)
                with tempfile.NamedTemporaryFile() as tmp:
                    ftp.retrbinary(f"RETR {ftp_path_full}", tmp.write)
                    tmp.flush()
                    tmp.seek(0)
                    zipf.writestr(filename, tmp.read())

        ftp.quit()
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"Коллекция_{id_collection}_фильтр_{year_from}_{year_to}.zip"
        )
    except Exception as e:
        print(f"FTP archive error: {e}")
        abort(500)


@app.errorhandler(400)
def handle_400(error):
    return render_template("400.html", error=error), 400


@app.errorhandler(404)
def handle_404(error):
    return render_template("404.html", error=error), 404


@app.errorhandler(403)
def handle_403(error):
    return render_template("400.html", error=error), 403


@app.errorhandler(500)
def handle_500(error):
    return render_template("500.html", error=error), 500


if __name__ == "__main__":
    app.config["SECRET_KEY"] = ""
    app.run(host="0.0.0.0", port=5000, debug=True)

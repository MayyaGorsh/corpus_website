from db import query_db


def get_all_nominations(query=None):
    """
    Получает список всех номинаций из таблицы PROFESSION_entry_area.
    """
    if query:
        return query_db("""
            SELECT id_entry_area AS id, nomination AS word, noun_gender AS gender, frequency
            FROM `PROFESSION_entry_area`
            WHERE LOWER(nomination) LIKE %s
            ORDER BY nomination ASC
        """, (f"%{query.lower()}%",))
    else:
        return query_db("""
            SELECT id_entry_area AS id, nomination AS word, noun_gender AS gender, frequency
            FROM `PROFESSION_entry_area`
            ORDER BY nomination ASC
        """)


def get_nomination_full(nomination_id):
    """
    Возвращает все данные по одной номинации, включая толкование, грамматический род,
    происхождение, словообразование, дискурс и примеры.
    """
    data = {}

    # Основные данные
    entry = query_db("""
        SELECT id_entry_area AS id, nomination, noun_gender AS gender, frequency 
        FROM `PROFESSION_entry_area`
        WHERE id_entry_area = %s;
    """, (nomination_id,))
    if not entry:
        return None

    row = entry[0]
    data["id"] = row["id"]
    data["word"] = row["nomination"]
    data["gender"] = row["gender"]
    data["frequency"] = row["frequency"]

    # Толкование и примеры
    definitions_raw = query_db("""
        SELECT id_interpretation_zone AS id,
               type AS status,
               interpretation AS definition,
               source_of_interpretation AS source
        FROM `PROFESSION_interpretation_zone`
        WHERE id_nomination = %s
        ORDER BY type = 'актуальный' DESC;
    """, (nomination_id,))

    definitions = []
    for d in definitions_raw:
        examples = query_db("""
            SELECT example, source_of_example AS source
            FROM `PROFESSION_example_of_interpretation_zone`
            WHERE id_interpretation_zone = %s;
        """, (d["id"],))
        d["examples"] = examples
        definitions.append(d)

    data["definitions"] = definitions

    # Примеры согласования
    data["gender_examples"] = query_db("""
        SELECT type AS label, example AS sentence, source
        FROM `PROFESSION_grammatical_gender_zone`
        WHERE id_nomination = %s;
    """, (nomination_id,))

    # Происхождение
    data["origin"] = query_db("""
        SELECT origin, example, source_of_example AS source
        FROM `PROFESSION_zone_of_origin`
        WHERE id_nomination = %s;
    """, (nomination_id,))

    # Словообразование
    data["word_forms"] = query_db("""
        SELECT type AS correlate_type, correlate AS word_form, notes AS label, example AS sentence, source_of_example AS source
        FROM `PROFESSION_word_formation_zone`
        WHERE id_nomination = %s;
    """, (nomination_id,))

    # Дискурсивная зона
    disc_zone = query_db("""
        SELECT id_discource_zone AS id, description AS commentary
        FROM `PROFESSION_discource_zone`
        WHERE id_nomination = %s;
    """, (nomination_id,))
    if disc_zone:
        data["discource_zone"] = disc_zone[0]["commentary"]
        disc_id = disc_zone[0]["id"]
        data["discource_examples"] = query_db("""
            SELECT example AS sentence, source
            FROM `PROFESSION_discource_example`
            WHERE id_discource_zone = %s;
        """, (disc_id,))
    else:
        data["discource_zone"] = ""
        data["discource_examples"] = []

    return data

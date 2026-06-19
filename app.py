from flask import Flask, render_template, request, redirect, jsonify
from pony.orm import *
from datetime import date
import os

app = Flask(__name__)
db = Database()
os.makedirs("database", exist_ok = True)


class StudySesija(db.Entity):
    id = PrimaryKey(int, auto = True)
    kolegij = Required(str)
    datum = Required(date)
    sati = Required(float)
    tema = Required(str)


db.bind(
    provider = "sqlite",
    filename = "database/study_planer.sqlite",
    create_db = True)


db.generate_mapping(create_tables = True)


def sesija_to_dict(sesija):
    return {
        "id": sesija.id,
        "kolegij": sesija.kolegij,
        "datum": sesija.datum.strftime("%Y-%m-%d"),
        "sati": sesija.sati,
        "tema": sesija.tema
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sesije")
@db_session
def prikaz_sesija():
    sesije = select(s for s in StudySesija).order_by(lambda s: s.datum)[:]
    return render_template("sesije.html", sesije = sesije)


@app.route("/dodaj", methods = ["GET", "POST"])
@db_session
def dodaj_sesiju():
    if request.method == "POST":
        StudySesija(
            kolegij = request.form["kolegij"],
            datum = date.fromisoformat(request.form["datum"]),
            sati = float(request.form["sati"]),
            tema = request.form["tema"]
        )
        return redirect("/sesije")
    return render_template("dodaj.html")


@app.route("/uredi/<int:id>", methods = ["GET", "POST"])
@db_session
def uredi_sesiju(id):
    sesija = StudySesija.get(id = id)

    if sesija is None:
        return "Sesija nije pronađena", 404

    if request.method == "POST":
        sesija.kolegij = request.form["kolegij"]
        sesija.datum = date.fromisoformat(request.form["datum"])
        sesija.sati = float(request.form["sati"])
        sesija.tema = request.form["tema"]
        return redirect("/sesije")
    return render_template("uredi.html", sesija=sesija)


@app.route("/obrisi/<int:id>")
@db_session
def obrisi_sesiju(id):
    sesija = StudySesija.get(id = id)
    if sesija:
        sesija.delete()
    return redirect("/sesije")


@app.route("/statistika")
@db_session
def statistika():
    ukupno_sati = sum(s.sati for s in StudySesija.select())
    sati_po_kolegiju = {}

    for sesija in StudySesija.select():
        if sesija.kolegij not in sati_po_kolegiju:
            sati_po_kolegiju[sesija.kolegij] = 0
        sati_po_kolegiju[sesija.kolegij] += sesija.sati

    return render_template(
        "statistika.html",
        ukupno_sati = ukupno_sati,
        sati_po_kolegiju = sati_po_kolegiju
    )


@app.route("/api/sesije", methods = ["GET"])
@db_session
def api_sve_sesije():
    sesije = select(s for s in StudySesija)[:]
    return jsonify([sesija_to_dict(s) for s in sesije])


@app.route("/api/sesije/<int:id>", methods = ["GET"])
@db_session
def api_jedna_sesija(id):
    sesija = StudySesija.get(id = id)
    if sesija is None:
        return jsonify({"greska": "Sesija nije pronađena"}), 404
    return jsonify(sesija_to_dict(sesija))


@app.route("/api/sesije", methods = ["POST"])
@db_session
def api_dodaj_sesiju():
    podaci = request.json
    sesija = StudySesija(
        kolegij = podaci["kolegij"],
        datum = date.fromisoformat(podaci["datum"]),
        sati = float(podaci["sati"]),
        tema = podaci["tema"]
    )
    return jsonify(sesija_to_dict(sesija)), 201


@app.route("/api/sesije/<int:id>", methods = ["PUT"])
@db_session
def api_uredi_sesiju(id):
    sesija = StudySesija.get(id = id)
    if sesija is None:
        return jsonify({"greska": "Sesija nije pronađena"}), 404
    podaci = request.json
    sesija.kolegij = podaci["kolegij"]
    sesija.datum = date.fromisoformat(podaci["datum"])
    sesija.sati = float(podaci["sati"])
    sesija.tema = podaci["tema"]
    return jsonify(sesija_to_dict(sesija))


@app.route("/api/sesije/<int:id>", methods = ["DELETE"])
@db_session
def api_obrisi_sesiju(id):
    sesija = StudySesija.get(id=id)
    if sesija is None:
        return jsonify({"greska": "Sesija nije pronađena"}), 404
    sesija.delete()
    return jsonify({"poruka": "Sesija je obrisana"})


@app.route("/api/statistika/ukupno-sati", methods = ["GET"])
@db_session
def api_ukupno_sati():
    ukupno = sum(s.sati for s in StudySesija.select())
    return jsonify({"ukupno_sati": ukupno})


@app.route("/api/statistika/sati-po-kolegiju", methods = ["GET"])
@db_session
def api_sati_po_kolegiju():
    rezultat = {}

    for sesija in StudySesija.select():
        if sesija.kolegij not in rezultat:
            rezultat[sesija.kolegij] = 0
        rezultat[sesija.kolegij] += sesija.sati
    return jsonify(rezultat)


@app.route("/api/sesije/kolegij/<kolegij>", methods = ["GET"])
@db_session
def api_sesije_po_kolegiju(kolegij):
    sesije = select(s for s in StudySesija if s.kolegij == kolegij)[:]
    return jsonify([sesija_to_dict(s) for s in sesije])


@app.route("/api/sesije/datum/<datum>", methods = ["GET"])
@db_session
def api_sesije_po_datumu(datum):
    trazeni_datum = date.fromisoformat(datum)
    sesije = select(s for s in StudySesija if s.datum == trazeni_datum)[:]
    return jsonify([sesija_to_dict(s) for s in sesije])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
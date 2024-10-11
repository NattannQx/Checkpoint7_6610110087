import flask
from models import db, Note, Tag
from forms import NoteForm, TagForm

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

db.init_app(app)

def get_note_by_id(note_id):
    return db.session.execute(db.select(Note).where(Note.id == note_id)).scalars().first()

def get_tag_by_name(tag_name):
    return db.session.execute(db.select(Tag).where(Tag.name == tag_name)).scalars().first()

@app.route("/")
def index():
    notes = db.session.execute(db.select(Note).order_by(Note.title)).scalars()
    tags = db.session.execute(db.select(Tag).order_by(Tag.name)).scalars()
    return flask.render_template("index.html", notes=notes, tags=tags)

@app.route("/notes/<note_id>", methods=["GET", "POST"])
def note_view(note_id):
    form = NoteForm()
    note = get_note_by_id(note_id)
    if not note:
        return "Note not found", 404

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        note.tags = [get_tag_by_name(tag_name) or Tag(name=tag_name) for tag_name in form.tags.data]
        db.session.commit()
        return flask.redirect(flask.url_for('index'))

    return flask.render_template("note-view.html", note_title=note.title, note=note, tag=", ".join([tag.name for tag in note.tags]), form=form)

@app.route("/notes/<note_id>/delete", methods=["POST"])
def note_delete(note_id):
    note = get_note_by_id(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return flask.redirect(flask.url_for('index'))

@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(title=form.title.data, description=form.description.data)
        note.tags = [get_tag_by_name(tag_name) or Tag(name=tag_name) for tag_name in form.tags.data]
        db.session.add(note)
        db.session.commit()
        return flask.redirect(flask.url_for("index"))
    return flask.render_template("notes-create.html", form=form)

@app.route("/tags/<tag_name>", methods=["GET", "POST"])
def tags_view(tag_name):
    form = TagForm()
    tag = get_tag_by_name(tag_name)
    if not tag:
        return "Tag not found", 404

    if form.validate_on_submit():
        tag.name = form.tag.data
        db.session.commit()
        return flask.redirect(flask.url_for('index'))

    notes = db.session.execute(db.select(Note).where(Note.tags.any(id=tag.id))).scalars()
    return flask.render_template("tags-view.html", tag_name=tag_name, notes=notes, form=form)

@app.route("/tags/<tag_id>/delete", methods=["POST"])
def tag_delete(tag_id):
    tag = db.session.execute(db.select(Tag).where(Tag.id == tag_id)).scalars().first()
    if not tag or db.session.execute(db.select(Note).where(Note.tags.any(id=tag.id))).scalars().first():
        flask.flash("Cannot delete this tag because it is used in some notes.", "danger")
    else:
        db.session.delete(tag)
        db.session.commit()
        flask.flash("Tag deleted successfully.", "success")
    return flask.redirect(flask.url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)

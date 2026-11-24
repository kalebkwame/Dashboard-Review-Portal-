from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.cors import configure_cors
from app.database import Base, SessionLocal, engine
from app.models import Dashboard, Section, User
from app.routers.auth import router as auth_router
from app.routers.reviews import router as reviews_router
from app.routers.sections import router as sections_router
from app.routers.dashboards import router as dashboards_router
from app.routers.sharing import router as sharing_router

app = FastAPI(title="Dashboard Review Portal - Starter API")
configure_cors(app)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def frontend():
    return FileResponse("static/index.html")


@app.get("/shared/{token}")
def shared_frontend(token: str):
    return FileResponse("static/shared.html")


@app.get("/admin/invite/{token}")
def admin_invitation_frontend(token: str):
    return FileResponse("static/admin-invite.html")


@app.get("/reset-password/{token}")
def reset_password_frontend(token: str):
    return FileResponse("static/reset-password.html")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(sections_router)
app.include_router(reviews_router)
app.include_router(auth_router)
app.include_router(dashboards_router)
app.include_router(sharing_router)


Base.metadata.create_all(bind=engine)


def ensure_review_status_column():
    # Lightweight SQLite-safe schema guard for local development.
    with engine.connect() as connection:
        column_rows = connection.exec_driver_sql("PRAGMA table_info(reviews)").fetchall()
        column_names = {row[1] for row in column_rows}
        if "status" not in column_names:
            connection.exec_driver_sql(
                "ALTER TABLE reviews ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open'"
            )
            connection.commit()


def ensure_section_dashboard_column():
    # Existing section rows need a dashboard before the new relationship can be used.
    with engine.connect() as connection:
        column_rows = connection.exec_driver_sql("PRAGMA table_info(sections)").fetchall()
        column_names = {row[1] for row in column_rows}
        if "dashboard_id" not in column_names:
            connection.exec_driver_sql(
                "ALTER TABLE sections ADD COLUMN dashboard_id INTEGER"
            )
            connection.commit()


def ensure_section_chart_columns():
    chart_columns = {
        "chart_headline": "VARCHAR(100) NOT NULL DEFAULT ''",
        "chart_change": "VARCHAR(200) NOT NULL DEFAULT ''",
        "chart_labels": "TEXT NOT NULL DEFAULT '[]'",
        "chart_values": "TEXT NOT NULL DEFAULT '[]'",
    }
    with engine.connect() as connection:
        column_rows = connection.exec_driver_sql("PRAGMA table_info(sections)").fetchall()
        column_names = {row[1] for row in column_rows}
        for name, definition in chart_columns.items():
            if name not in column_names:
                connection.exec_driver_sql(
                    f"ALTER TABLE sections ADD COLUMN {name} {definition}"
                )
        connection.commit()


def seed_demo_dashboard(db):
    owner = db.query(User).filter(User.role == "admin").order_by(User.id).first()
    if not owner:
        owner = db.query(User).order_by(User.id).first()
    if not owner:
        return

    dashboard = db.query(Dashboard).filter(Dashboard.name == "Executive Overview").first()
    if not dashboard:
        dashboard = Dashboard(
            name="Executive Overview",
            description="High-level overview of key business metrics.",
            owner_id=owner.id,
        )
        db.add(dashboard)
        db.flush()

    demo_sections = {
        "Sales Overview": ("line", "$1.28M", "+18.4% vs prior period", ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [820, 910, 860, 1040, 1120, 1280]),
        "Customer Retention": ("bar", "92.4%", "+3.1 pts quarter over quarter", ["Enterprise", "Mid-market", "Small business", "Self-service"], [96, 93, 89, 84]),
        "Revenue by Region": ("pie", "$1.28M", "Top region: North America", ["North America", "Europe", "Asia Pacific", "Latin America"], [520, 310, 270, 180]),
        "Marketing Trend": ("line", "42.8K", "+24.6% qualified leads", ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [24, 27, 31, 29, 38, 43]),
        "Revenue Growth": ("bar", "+18.4%", "Year-over-year growth", ["Q1", "Q2", "Q3", "Q4"], [12, 15, 17, 18]),
        "Finance KPIs": ("bar", "38.2%", "Operating margin", ["Operating margin", "Gross margin", "EBITDA", "Cash reserve"], [38, 62, 29, 71]),
    }

    existing_names = {section.name for section in db.query(Section).filter(Section.dashboard_id == dashboard.id).all()}
    for name, (chart_type, headline, change, labels, values) in demo_sections.items():
        if name not in existing_names:
            db.add(Section(dashboard_id=dashboard.id, name=name, chart_type=chart_type, chart_headline=headline, chart_change=change, chart_labels=labels, chart_values=values))
    db.commit()


with SessionLocal() as startup_db:
    seed_demo_dashboard(startup_db)

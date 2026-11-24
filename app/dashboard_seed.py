from sqlalchemy.orm import Session

from app.models import Dashboard, Section, User


DEMO_SECTIONS = {
    "Sales Overview": ("line", "$1.28M", "+18.4% vs prior period", ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [820, 910, 860, 1040, 1120, 1280]),
    "Customer Retention": ("bar", "92.4%", "+3.1 pts quarter over quarter", ["Enterprise", "Mid-market", "Small business", "Self-service"], [96, 93, 89, 84]),
    "Revenue by Region": ("pie", "$1.28M", "Top region: North America", ["North America", "Europe", "Asia Pacific", "Latin America"], [520, 310, 270, 180]),
    "Marketing Trend": ("line", "42.8K", "+24.6% qualified leads", ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], [24, 27, 31, 29, 38, 43]),
    "Revenue Growth": ("bar", "+18.4%", "Year-over-year growth", ["Q1", "Q2", "Q3", "Q4"], [12, 15, 17, 18]),
    "Finance KPIs": ("bar", "38.2%", "Operating margin", ["Operating margin", "Gross margin", "EBITDA", "Cash reserve"], [38, 62, 29, 71]),
}


def seed_demo_dashboard(db: Session, owner: User) -> Dashboard:
    dashboard = db.query(Dashboard).filter(Dashboard.name == "Executive Overview").first()
    if not dashboard:
        dashboard = Dashboard(
            name="Executive Overview",
            description="High-level overview of key business metrics.",
            owner_id=owner.id,
        )
        db.add(dashboard)
        db.flush()

    existing_names = {
        section.name
        for section in db.query(Section).filter(Section.dashboard_id == dashboard.id).all()
    }
    for name, (chart_type, headline, change, labels, values) in DEMO_SECTIONS.items():
        if name not in existing_names:
            db.add(Section(
                dashboard_id=dashboard.id,
                name=name,
                chart_type=chart_type,
                chart_headline=headline,
                chart_change=change,
                chart_labels=labels,
                chart_values=values,
            ))
    db.commit()
    db.refresh(dashboard)
    return dashboard

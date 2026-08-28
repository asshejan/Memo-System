"""Seed two isolated demo organizations so the tenant-isolation and full workflow
demonstration scenario (spec section 28) can be run immediately after setup.

Usage:  python -m app.seed
"""
from app.db import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.department import Department
from app.models.user import User
from app.models.category import MemoCategory
from app.models.workflow_template import WorkflowTemplate, WorkflowTemplatePosition
from app.models.enums import UserRole

DEMO_PASSWORD = "Password123!"


def seed_org(db, *, name: str, identifier: str) -> dict:
    org = Organization(name=name, identifier=identifier, contact_email=f"admin@{identifier}.example")
    db.add(org)
    db.flush()

    dept_ops = Department(organization_id=org.id, name="Operations")
    dept_finance = Department(organization_id=org.id, name="Finance")
    dept_hr = Department(organization_id=org.id, name="Human Resources")
    db.add_all([dept_ops, dept_finance, dept_hr])
    db.flush()

    admin = User(
        organization_id=org.id,
        name=f"{name} Admin",
        email=f"admin@{identifier}.example",
        password_hash=hash_password(DEMO_PASSWORD),
        designation="Administrator",
        department_id=dept_ops.id,
        role=UserRole.org_admin,
    )
    employee = User(
        organization_id=org.id,
        name="Employee One",
        email=f"employee@{identifier}.example",
        password_hash=hash_password(DEMO_PASSWORD),
        designation="Staff",
        department_id=dept_ops.id,
        role=UserRole.regular_user,
    )
    dept_head = User(
        organization_id=org.id,
        name="Department Head",
        email=f"depthead@{identifier}.example",
        password_hash=hash_password(DEMO_PASSWORD),
        designation="Department Head",
        department_id=dept_ops.id,
        role=UserRole.regular_user,
    )
    finance_manager = User(
        organization_id=org.id,
        name="Finance Manager",
        email=f"finance@{identifier}.example",
        password_hash=hash_password(DEMO_PASSWORD),
        designation="Finance Manager",
        department_id=dept_finance.id,
        role=UserRole.regular_user,
    )
    director = User(
        organization_id=org.id,
        name="Director",
        email=f"director@{identifier}.example",
        password_hash=hash_password(DEMO_PASSWORD),
        designation="Director",
        department_id=dept_ops.id,
        role=UserRole.regular_user,
    )
    db.add_all([admin, employee, dept_head, finance_manager, director])
    db.flush()

    for cat_name in ["Administrative", "Financial", "Procurement", "HR", "Technical", "General"]:
        db.add(MemoCategory(organization_id=org.id, name=cat_name))

    template = WorkflowTemplate(organization_id=org.id, name="Purchase Request")
    template.positions = [
        WorkflowTemplatePosition(position_index=0, label="Department Head"),
        WorkflowTemplatePosition(position_index=1, label="Finance Manager"),
        WorkflowTemplatePosition(position_index=2, label="Director"),
    ]
    db.add(template)

    db.commit()

    return {
        "org": org,
        "admin": admin,
        "employee": employee,
        "dept_head": dept_head,
        "finance_manager": finance_manager,
        "director": director,
    }


def main():
    Base.metadata.create_all(bind=engine)  # safety net if migrations haven't been run
    db = SessionLocal()
    try:
        acme = seed_org(db, name="Acme Corporation", identifier="acme")
        globex = seed_org(db, name="Globex Inc", identifier="globex")

        print("Seed complete. Demo password for every account:", DEMO_PASSWORD)
        for label, bundle in (("Acme", acme), ("Globex", globex)):
            print(f"\n{label} ({bundle['org'].identifier}):")
            for role in ["admin", "employee", "dept_head", "finance_manager", "director"]:
                print(f"  {role:14s} {bundle[role].email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

#done
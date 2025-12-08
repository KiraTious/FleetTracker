from flask import Blueprint, redirect, render_template, url_for


frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def index():
    return redirect(url_for("frontend.login"))


@frontend_bp.route("/login")
def login():
    return render_template("login.html")


@frontend_bp.route("/portal/admin")
def admin_portal():
    return render_template("admin_dashboard.html")


@frontend_bp.route("/portal/manager")
def manager_portal():
    return render_template("manager_dashboard.html")


@frontend_bp.route("/portal/driver")
def driver_portal():
    return render_template("driver_dashboard.html")

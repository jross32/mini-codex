import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

# --------------------------------------------------------------------------- #
# App setup
# --------------------------------------------------------------------------- #

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///whatapc.db")
cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
if cors_origins_raw == "*":
    CORS_ORIGINS = "*"
else:
    CORS_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app, origins=CORS_ORIGINS)

engine = create_engine(DB_URL, echo=False, future=True)
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    image = Column(String(255), default="")
    gpu = Column(String(80))
    cpu = Column(String(80))
    memory = Column(String(80))
    storage = Column(String(120))
    use_case = Column(String(120))
    badge = Column(String(40))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CustomBuildRequest(Base):
    __tablename__ = "custom_build_requests"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False)
    budget = Column(Float)
    primary_use = Column(String(120))
    preferences = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# --------------------------------------------------------------------------- #
# Seed helpers
# --------------------------------------------------------------------------- #

def seed_data(session):
    if session.query(Product).count() == 0:
        session.add_all(
            [
                Product(
                    name="Wraith X1",
                    category="Ready-To-Game",
                    description="1080p esports rocket with headroom for streaming.",
                    price=999,
                    image="https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80",
                    gpu="RTX 4060",
                    cpu="Ryzen 5 7600",
                    memory="16GB DDR5",
                    storage="1TB NVMe Gen4",
                    use_case="Esports / Creator Starter",
                    badge="Best Value",
                ),
                Product(
                    name="Nebula Pro",
                    category="Creator",
                    description="4K-capable workstation tuned for Adobe + Blender.",
                    price=1999,
                    image="https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=1200&q=80",
                    gpu="RTX 4070 Ti Super",
                    cpu="Ryzen 7 7800X3D",
                    memory="32GB DDR5",
                    storage="2TB NVMe Gen4",
                    use_case="4K Video / 3D",
                    badge="Creator Pick",
                ),
                Product(
                    name="Titan Apex",
                    category="Enthusiast",
                    description="Maxed-out thermal headroom, liquid cooled, VR-ready.",
                    price=3299,
                    image="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1200&q=80",
                    gpu="RTX 4090",
                    cpu="Intel i9-14900K",
                    memory="64GB DDR5",
                    storage="2TB NVMe Gen4 + 4TB SSD",
                    use_case="VR / AI / 8K",
                    badge="Flagship",
                ),
            ]
        )

    if session.query(FAQ).count() == 0:
        session.add_all(
            [
                FAQ(
                    question="How long does it take to build and ship?",
                    answer="Most ready-to-ship builds leave our lab in 3 business days. Custom requests average 7–10 business days.",
                ),
                FAQ(
                    question="Do you offer warranty and support?",
                    answer="Every WhatAPC system includes a 2-year parts and labor warranty plus lifetime chat support.",
                ),
                FAQ(
                    question="Can I upgrade later?",
                    answer="Absolutely. We design with standard parts and roomy cases. We can also handle upgrades for you.",
                ),
            ]
        )

    session.commit()


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@app.teardown_appcontext
def remove_session(exception=None):
    Session.remove()


@app.route("/api/products", methods=["GET"])
def list_products():
    session = Session()
    products = session.query(Product).order_by(Product.price).all()
    return jsonify([p.to_dict() for p in products])


@app.route("/api/faqs", methods=["GET"])
def list_faqs():
    session = Session()
    faqs = session.query(FAQ).all()
    return jsonify([f.to_dict() for f in faqs])


@app.route("/api/custom-builds", methods=["POST"])
def create_custom_build():
    session = Session()
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    budget = data.get("budget")
    primary_use = data.get("primary_use")
    preferences = data.get("preferences", "")

    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    build = CustomBuildRequest(
        name=name,
        email=email,
        budget=budget,
        primary_use=primary_use,
        preferences=preferences,
    )
    session.add(build)
    session.commit()
    return jsonify(build.to_dict()), 201


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# --------------------------------------------------------------------------- #
# CLI entry
# --------------------------------------------------------------------------- #

def init_db():
    Base.metadata.create_all(engine)
    session = Session()
    seed_data(session)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

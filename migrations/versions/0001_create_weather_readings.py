"""create weather_readings

Revision ID: 0001
Revises:
Create Date: 2026-11-22 18:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEMPERATURE = sa.Numeric(6, 2)
COORDINATE = sa.Numeric(8, 5)


def upgrade() -> None:
    op.create_table(
        "weather_readings",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False, comment="OpenWeather city id"),
        sa.Column(
            "city_name", sa.Text(), nullable=False, comment="City name as returned by OpenWeather"
        ),
        sa.Column(
            "city_search_name",
            sa.Text(),
            nullable=False,
            comment="Lower-cased, accent-free city name used for lookups",
        ),
        sa.Column("country_code", sa.String(length=2), nullable=True, comment="ISO 3166-1 alpha-2"),
        sa.Column("latitude", COORDINATE, nullable=False),
        sa.Column("longitude", COORDINATE, nullable=False),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When OpenWeather measured the data (dt)",
        ),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="When this service last collected the observation",
        ),
        sa.Column("units", sa.Text(), nullable=False, comment="Unit system of the measurements"),
        sa.Column("lang", sa.Text(), nullable=False, comment="Language of weather_description"),
        sa.Column("temperature", TEMPERATURE, nullable=False),
        sa.Column("feels_like", TEMPERATURE, nullable=False),
        sa.Column("temp_min", TEMPERATURE, nullable=False),
        sa.Column("temp_max", TEMPERATURE, nullable=False),
        sa.Column("humidity", sa.SmallInteger(), nullable=False, comment="%"),
        sa.Column("pressure", sa.SmallInteger(), nullable=False, comment="hPa"),
        sa.Column("wind_speed", sa.Numeric(6, 2), nullable=False),
        sa.Column("wind_deg", sa.SmallInteger(), nullable=True, comment="Degrees"),
        sa.Column("cloudiness", sa.SmallInteger(), nullable=False, comment="%"),
        sa.Column("weather_main", sa.Text(), nullable=False, comment="e.g. Clouds"),
        sa.Column("weather_description", sa.Text(), nullable=False, comment="e.g. nublado"),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Original OpenWeather response, for auditing and reprocessing",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weather_readings")),
        sa.UniqueConstraint(
            "city_id",
            "observed_at",
            "units",
            name=op.f("uq_weather_readings_city_id_observed_at_units"),
        ),
        sa.CheckConstraint(
            "units IN ('standard', 'metric', 'imperial')",
            name=op.f("ck_weather_readings_units_valid"),
        ),
        sa.CheckConstraint(
            "humidity BETWEEN 0 AND 100", name=op.f("ck_weather_readings_humidity_percent")
        ),
        sa.CheckConstraint(
            "cloudiness BETWEEN 0 AND 100", name=op.f("ck_weather_readings_cloudiness_percent")
        ),
        sa.CheckConstraint(
            "wind_deg BETWEEN 0 AND 360", name=op.f("ck_weather_readings_wind_deg_range")
        ),
        sa.CheckConstraint(
            "latitude BETWEEN -90 AND 90", name=op.f("ck_weather_readings_latitude_range")
        ),
        sa.CheckConstraint(
            "longitude BETWEEN -180 AND 180", name=op.f("ck_weather_readings_longitude_range")
        ),
        comment="Current weather observations collected from OpenWeather",
    )
    op.create_index(
        "ix_weather_readings_city_search_observed_at",
        "weather_readings",
        ["city_search_name", "observed_at"],
    )
    op.create_index("ix_weather_readings_observed_at", "weather_readings", ["observed_at"])


def downgrade() -> None:
    op.drop_index("ix_weather_readings_observed_at", table_name="weather_readings")
    op.drop_index("ix_weather_readings_city_search_observed_at", table_name="weather_readings")
    op.drop_table("weather_readings")

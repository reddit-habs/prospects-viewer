from datetime import date

from sqlalchemy import Boolean, Column, Integer, Float, Text, Date, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from .dto import Position, Shoots

Base = declarative_base()


class Draft(Base):
    __tablename__ = "draft"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"), index=True)
    player = relationship("Player", back_populates="drafts")

    year = Column(Integer)
    round = Column(Integer)
    overall = Column(Integer)
    team = Column(Text)


class StatLine(Base):
    __tablename__ = "stat_line"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"), index=True)
    player = relationship("Player", back_populates="stats")

    season_begin = Column(Integer)
    season_end = Column(Integer)
    team_name = Column(Text)
    league_name = Column(Text)
    games = Column(Integer)
    is_tournament = Column(Boolean)

    # skater
    goals = Column(Integer)
    assists = Column(Integer)
    plus_minus = Column(Integer)

    # goalie
    goal_average = Column(Float)
    save_percent = Column(Float)

    @property
    def points(self):
        if self.goals is None or self.assists is None:
            return None
        return self.goals + self.assists


class Player(Base):
    __tablename__ = "player"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(Text)
    birthday = Column(Date)
    nation = Column(Text)
    birthplace = Column(Text)

    position = Column(Enum(Position))
    shoots = Column(Enum(Shoots))
    height = Column(Text)
    height_cm = Column(Integer)
    weight = Column(Text)
    weight_kg = Column(Integer)

    url = Column(Text)
    scouting_report = Column(Text)

    drafts = relationship("Draft", back_populates="player", lazy="dynamic")
    stats = relationship("StatLine", back_populates="player", lazy="dynamic")

    @property
    def age(self):
        age_delta = date.today() - self.birthday
        return round(age_delta.days / 365.242199, 1)

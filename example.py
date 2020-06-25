from sqlalchemy import Column, Integer, DateTime, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy_column_flag import column_flag

Base = declarative_base()


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    published_at = Column("publication_date", DateTime)
    is_published = column_flag(published_at, default=func.now())


def main():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)

    art1 = Article(content="First post", published_at=func.now())
    art2 = Article(content="Tentative content")
    session.add_all([art1, art2])
    session.flush()
    count_total = session.query(Article).count()
    count_published = session.query(Article).filter(Article.is_published).count()
    print(f"Articles published out of total: {count_published}/{count_total}")

    assert art1.is_published
    assert not art2.is_published

    # Publish article 2
    assert art2.published_at is None
    print("\nSetting `is_published` to True on unpublished article")
    art2.is_published = True
    session.flush()
    assert art2.published_at is not None
    print(f"Article was published at {art2.published_at}")

    # Unpublish article 2
    print("\nSetting `is_published` to False on published article")
    art2.is_published = False
    session.flush()
    assert art2.published_at is None
    print(f"Article publication date: {art2.published_at}")


if __name__ == "__main__":
    main()

from pydantic import BaseModel, Field

from quotes_recommender.core.models import QuoteData


class UserItem(BaseModel):
    """Item defining a scraped user profile."""

    user_id: int = Field(description="Unique identifier of a user.")
    user_name: str = Field(description="The name of the user.")


class ExtendedQuoteData(QuoteData):
    """Defining data model for quote (meta) data."""

    author: str = Field(description="Name of the quote author")
    author_profile: str = Field(description="Information page of the quote author")
    avatar_img: str = Field(description="Embedded link to avatar image.")
    num_likes: int = Field(description="Number of likes the quote received.")
    feed_url: str = Field(description="The URL to the quote's feed.")
    tags: list[str] = Field(description="List of tags the quote got assigned to.")
    liking_users: list[UserItem] = Field(description="List of users that liked the quote.")


class QuoteItem(BaseModel):
    """Item defining a scraped quote."""

    id: int = Field(description="The unique ID of the quote.")
    data: ExtendedQuoteData = Field(description="(Meta) data of the quote.")

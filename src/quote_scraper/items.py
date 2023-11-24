from pydantic import Field
from scrapy import Item, Field
from yarl import URL


class UserItem(Item):
    """Item defining a scraped user profile."""

    user_id: int = Field(description="Unique identifier of a user.")
    username: str = Field(description="The name of the user.")


class QuoteData(Item):
    """Defining data model for quote (meta) data."""

    author: str = Field(description="Name of the author")
    avatar_img: URL = Field(description="Embedded link to avatar image.", serialize=True)
    avatar: URL = Field(description="")  # TODO: add appropriate description
    text: str = Field(description="The actual quote.")
    num_likes: int = Field(description="Number of likes the quote received.")
    feed_url: URL = Field(description="The URL to the quote's feed.", serialize=True)
    tags: list[str] = Field(description="List of tags the quote got assigned to.")
    liking_users: list[UserItem] = Field(description="List of users that liked the quote.")


class QuoteItem(Item):
    """Item defining a scraped quote."""

    id: int = Field(description="The unique ID of the quote.")
    data: QuoteData = Field(description="(Meta) data of the quote.")

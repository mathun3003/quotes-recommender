from scrapy import Item
from scrapy.item import Field


class UserItem(Item):
    """Item defining a scraped user profile."""

    user_id: int = Field(description="Unique identifier of a user.")
    username: str = Field(description="The name of the user.")


class QuoteItem(Item):
    """Item defining a scraped quote."""

    author: str = Field(description="Name of the author")
    avatar_img: str = Field(description="Embedded link to avatar image.", serialize=True)
    avatar: str = Field(description="")  # TODO: add appropriate description
    text: str = Field(description="The actual quote.")
    num_likes: int = Field(description="Number of likes the quote received.")
    feed_url: str = Field(description="The URL to the quote's feed.", serialize=True)
    tags: list[str] = Field(description="List of tags the quote got assigned to.")
    liking_users: list[UserItem] = Field(description="List of users that liked the quote.")

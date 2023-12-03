from pydantic import BaseModel, Field

class User(BaseModel):
    """Item defining a scraped user profile."""

    user_id: int = Field(description="Unique identifier of a user.")
    user_name: str = Field(description="The name of the user.")

class QuoteData(BaseModel):
    """Defining data model for quote (meta) data."""

    author_name: str = Field(description="Name of the author")
    author_page: str = Field(description="Information page of the quote author")
    avatar_img: str = Field(description="Embedded link to avatar image.", serialize=True)
    quote: str = Field(description="The actual quote.")
    num_likes: int = Field(description="Number of likes the quote received.")
    feed_url: str = Field(description="The URL to the quote's feed.", serialize=True)
    tags: list[str] = Field(description="List of tags the quote got assigned to.")
    liking_users: list[User] = Field(description="List of users that liked the quote.")

class Quote(BaseModel):
    """Item defining a scraped quote."""

    id: int = Field(description="The unique ID of the quote.")
    data: QuoteData = Field(description="(Meta) data of the quote.")

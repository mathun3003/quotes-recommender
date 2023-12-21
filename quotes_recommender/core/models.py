from pydantic import BaseModel, Extra, Field


class ForbidExtraModel(BaseModel):
    """Class configuring the BaseModel by forbid extra fields."""

    class Config:
        """Model configs"""

        extra = Extra.forbid


class QuoteData(ForbidExtraModel):
    """Class representing data of a quote that gets displayed to the user."""

    id: int = Field(description="The ID under which the quote is stored in the database.")
    text: str = Field(description="The text of the quote.")
    author: str = Field(description="The author of the quote.")
    tags: list[str] = Field(description="The list of tags assigned to the quote.")


class UserPreference(ForbidExtraModel):
    """Class representing a user preference regarding a quote."""

    id: int = Field(description="The ID under which the quote is stored in the database.", ge=1)
    like: bool = Field(description="Whether the user preference was a like.")

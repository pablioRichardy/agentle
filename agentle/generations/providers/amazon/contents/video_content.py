# Video content block
from typing import TypedDict

from agentle.generations.providers.amazon.contents.video_block import VideoBlock


class VideoContent(TypedDict):
    video: VideoBlock

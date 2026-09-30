"""Example EduTeX extension: add a reading tip after Layout Processing."""

from copy import deepcopy

from edutex.extension.models import ExtensionContext
from edutex.knowledge.models import TextBlock


def apply(context: ExtensionContext):
    """Return a new document containing a short reading tip at the beginning."""
    document = deepcopy(context.document)
    document.prose_blocks.append(
        (
            -1,
            TextBlock(
                content=(
                    "**Reading tip:** Notice how the verb ending changes with "
                    "the subject."
                )
            ),
        )
    )
    return document

import logging

from . import Variable

logger = logging.getLogger("django.template")


def default_invalid_variable_handler(context, reason, variable=None, **kwargs):
    try:
        variable_name = kwargs["bit"]
    except KeyError:
        if variable and isinstance(variable, Variable):
            variable_name = variable.var
        else:
            variable_name = "unknown"

    template_name = getattr(context, "template_name", None) or "unknown"
    logger.debug(
        "Exception while resolving variable '%s' in template '%s'.",
        variable_name,
        template_name,
        exc_info=True,
    )

    try:
        # This line is included for anyone who is relying on `string_if_invalid
        # to do something.
        string_if_invalid = kwargs["string_if_invalid"]
    except KeyError:
        try:
            # When `string_if_invalid` is removed, we can delete this line.
            string_if_invalid = context.template.engine.string_if_invalid
        except AttributeError:
            string_if_invalid = ""

    if "%s" in string_if_invalid and variable_name is not None:
        return string_if_invalid % variable_name
    else:
        return string_if_invalid


class BaseInvalidVariableType:
    """
    Base class for custom behaviour when a template has an invalid variable.

    There are 3 main methods that can be overridden:
    - handle_{reason} / handle() - called when the DTL encounters the invalid
      variable.
    - render_{reason} / render() - called when the DTL actually renders the
      invalid variable.
    - should_apply_filters() - to determine if filters should first be applied
      before 'rendering'.

    There are also a few properties provided as a convenience for writing error
    messages:
     - template
     - template_name
     - variable_name
    """

    def __init__(self, variable, context, reason, **kwargs):
        self.variable = variable
        self.context = context
        self.reason = reason
        self.bit = kwargs.get("bit")
        method = getattr(self, f"handle_{self.reason}", None)
        if callable(method):
            method()
        else:
            self.handle()

    @property
    def template(self):
        try:
            return self.context.template
        except AttributeError:
            return None

    @property
    def template_name(self):
        return getattr(self.context, "template_name", None) or "unknown"

    @property
    def variable_name(self):
        if isinstance(self.variable, Variable):
            return self.variable.var
        if callable(self.variable):
            if hasattr(self.variable, "__name__"):
                return self.variable.__name__
            if hasattr(self.variable, "__qualname__"):
                return self.variable.__qualname__
            if hasattr(self.variable, "__class__"):
                return self.variable.__class__.__name__
        return "unknown"

    def should_apply_filters(self):
        return True

    def render(self):
        return ""

    def render_silent_variable_failure(self):
        return ""

    def handle(self):
        pass

    def __str__(self):
        method = getattr(self, f"render_{self.reason}", None)
        if callable(method):
            return method()
        return self.render()

    def __bool__(self):
        return not self.should_apply_filters()

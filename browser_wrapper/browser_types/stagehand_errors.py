"""
Stagehand error classes
"""

from typing import Any, List, Optional

from browser_wrapper.version import STAGEHAND_VERSION


class StagehandError(Exception):
    """Base Stagehand error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.name = self.__class__.__name__

class StagehandDefaultError(StagehandError):
    """Default Stagehand error with version info"""
    
    def __init__(self, error: Optional[Any] = None) -> None:
        if isinstance(error, (Exception, StagehandError)):
            message = f"""
Hey! We're sorry you ran into an error.
Stagehand version: {STAGEHAND_VERSION}
If you need help, please open a Github issue or reach out to us on Slack: https://stagehand.dev/slack

Full error:
{str(error)}
"""
        else:
            message = "An unknown error occurred"
        super().__init__(message)

class StagehandEnvironmentError(StagehandError):
    """Environment configuration error"""
    
    def __init__(self, current_environment: str, required_environment: str, feature: str) -> None:
        message = (
            f"You seem to be setting the current environment to {current_environment}. "
            f"Ensure the environment is set to {required_environment} if you want to use {feature}."
        )
        super().__init__(message)

class MissingEnvironmentVariableError(StagehandError):
    """Missing environment variable error"""
    
    def __init__(self, missing_environment_variable: str, feature: str) -> None:
        message = (
            f"{missing_environment_variable} is required to use {feature}. "
            f"Please set {missing_environment_variable} in your environment."
        )
        super().__init__(message)

class UnsupportedModelError(StagehandError):
    """Unsupported model error"""
    
    def __init__(self, supported_models: List[str], feature: Optional[str] = None) -> None:
        if feature:
            message = f"{feature} requires one of the following models: {supported_models}"
        else:
            message = f"please use one of the supported models: {supported_models}"
        super().__init__(message)

class UnsupportedModelProviderError(StagehandError):
    """Unsupported model provider error"""
    
    def __init__(self, supported_providers: List[str], feature: Optional[str] = None) -> None:
        if feature:
            message = f"{feature} requires one of the following model providers: {supported_providers}"
        else:
            message = f"please use one of the supported model providers: {supported_providers}"
        super().__init__(message)

class UnsupportedAISDKModelProviderError(StagehandError):
    """Unsupported AI SDK model provider error"""
    
    def __init__(self, provider: str, supported_providers: List[str]) -> None:
        message = (
            f"{provider} is not currently supported for aiSDK. "
            f"please use one of the supported model providers: {supported_providers}"
        )
        super().__init__(message)

class InvalidAISDKModelFormatError(StagehandError):
    """Invalid AI SDK model format error"""
    
    def __init__(self, model_name: str) -> None:
        message = (
            f"{model_name} does not follow correct format for specifying aiSDK models. "
            f"Please define your modelName as 'provider/model-name'. "
            f"For example: `modelName: 'openai/gpt-4o-mini'`"
        )
        super().__init__(message)

class StagehandNotInitializedError(StagehandError):
    """Stagehand not initialized error"""
    
    def __init__(self, prop: str) -> None:
        message = (
            f"You seem to be calling `{prop}` on a page in an uninitialized `Stagehand` object. "
            f"Ensure you are running `await stagehand.init()` on the Stagehand object before "
            f"referencing the `page` object."
        )
        super().__init__(message)

class BrowserbaseSessionNotFoundError(StagehandError):
    """Browserbase session not found error"""
    
    def __init__(self) -> None:
        super().__init__("No Browserbase session ID found")

class CaptchaTimeoutError(StagehandError):
    """Captcha timeout error"""
    
    def __init__(self) -> None:
        super().__init__("Captcha timeout")

class MissingLLMConfigurationError(StagehandError):
    """Missing LLM configuration error"""
    
    def __init__(self) -> None:
        message = (
            "No LLM API key or LLM Client configured. An LLM API key or a custom LLM Client "
            "is required to use act, extract, or observe."
        )
        super().__init__(message)

class HandlerNotInitializedError(StagehandError):
    """Handler not initialized error"""
    
    def __init__(self, handler_type: str) -> None:
        super().__init__(f"{handler_type} handler not initialized")

class StagehandInvalidArgumentError(StagehandError):
    """Invalid argument error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"InvalidArgumentError: {message}")

class StagehandElementNotFoundError(StagehandError):
    """Element not found error"""
    
    def __init__(self, xpaths: List[str]) -> None:
        super().__init__(f"Could not find an element for the given xPath(s): {xpaths}")

class AgentScreenshotProviderError(StagehandError):
    """Screenshot provider error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"ScreenshotProviderError: {message}")

class StagehandMissingArgumentError(StagehandError):
    """Missing argument error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"MissingArgumentError: {message}")

class CreateChatCompletionResponseError(StagehandError):
    """Chat completion response error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"CreateChatCompletionResponseError: {message}")

class StagehandEvalError(StagehandError):
    """Evaluation error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"StagehandEvalError: {message}")

class StagehandDomProcessError(StagehandError):
    """DOM processing error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(f"Error Processing Dom: {message}")

class StagehandClickError(StagehandError):
    """Click error"""
    
    def __init__(self, message: str, selector: str) -> None:
        super().__init__(f"Error Clicking Element with selector: {selector} Reason: {message}")

class LLMResponseError(StagehandError):
    """LLM response error"""
    
    def __init__(self, primitive: str, message: str) -> None:
        super().__init__(f"{primitive} LLM response error: {message}")

class StagehandIframeError(StagehandError):
    """Iframe error"""
    
    def __init__(self, frame_url: str, message: str) -> None:
        super().__init__(f"Unable to resolve frameId for iframe with URL: {frame_url} Full error: {message}")

class ContentFrameNotFoundError(StagehandError):
    """Content frame not found error"""
    
    def __init__(self, selector: str) -> None:
        super().__init__(f"Unable to obtain a content frame for selector: {selector}")

class XPathResolutionError(StagehandError):
    """XPath resolution error"""
    
    def __init__(self, xpath: str) -> None:
        super().__init__(f'XPath "{xpath}" does not resolve in the current page or frames')

class ExperimentalApiConflictError(StagehandError):
    """Experimental API conflict error"""
    
    def __init__(self) -> None:
        message = (
            "`experimental` mode cannot be used together with the Stagehand API. "
            "To use experimental features, set experimental: true, and useApi: false in the stagehand constructor. "
            "To use the Stagehand API, set experimental: false and useApi: true in the stagehand constructor."
        )
        super().__init__(message)

class ExperimentalNotConfiguredError(StagehandError):
    """Experimental not configured error"""
    
    def __init__(self, feature_name: str) -> None:
        message = (
            f'Feature "{feature_name}" is an experimental feature, and cannot be configured when useAPI: true.\n'
            f"Please set experimental: true and useAPI: false in the stagehand constructor to use this feature.\n"
            f"If you wish to use the Stagehand API, please ensure {feature_name} is not defined in your function call,\n"
            f"and set experimental: false, useAPI: true in the Stagehand constructor."
        )
        super().__init__(message)

class ZodSchemaValidationError(Exception):
    """Schema validation error"""
    
    def __init__(self, received: Any, issues: Any) -> None:
        message = f"""Zod schema validation failed

— Received —
{received}

— Issues —
{issues}"""
        super().__init__(message)
        self.name = "ZodSchemaValidationError"

class StagehandInitError(StagehandError):
    """Initialization error"""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)

class MCPConnectionError(StagehandError):
    """MCP connection error"""
    
    def __init__(self, server_url: str, original_error: Any) -> None:
        error_message = str(original_error) if isinstance(original_error, Exception) else str(original_error)
        message = (
            f'Failed to connect to MCP server at "{server_url}". {error_message}. '
            f"Please verify the server URL is correct and the server is running."
        )
        super().__init__(message)
        self.server_url = server_url
        self.original_error = original_error

class StagehandShadowRootMissingError(StagehandError):
    """Shadow root missing error"""
    
    def __init__(self, detail: Optional[str] = None) -> None:
        message = "No shadow root present on the resolved host"
        if detail:
            message += f": {detail}"
        super().__init__(message)

class StagehandShadowSegmentEmptyError(StagehandError):
    """Shadow segment empty error"""
    
    def __init__(self) -> None:
        super().__init__('Empty selector segment after shadow-DOM hop ("//")')

class StagehandShadowSegmentNotFoundError(StagehandError):
    """Shadow segment not found error"""
    
    def __init__(self, segment: str, hint: Optional[str] = None) -> None:
        message = f"Shadow segment '{segment}' matched no element inside shadow root"
        if hint:
            message += f" {hint}"
        super().__init__(message)

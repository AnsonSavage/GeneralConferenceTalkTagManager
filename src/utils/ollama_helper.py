"""
Ollama integration for automatic tag suggestions using Pydantic for structured output.
"""
import ollama
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import streamlit as st


class TagSuggestion(BaseModel):
    """A single tag suggestion with reasoning and confidence."""
    reasoning: str = Field(description="Detailed explanation of why this tag is relevant to the paragraph")
    tag_name: str = Field(description="The exact name of the suggested tag from the available tags")
    confidence: str = Field(description="Confidence level: high, medium, or low", pattern="^(high|medium|low)$")


class TagSuggestionsResponse(BaseModel):
    """Response containing tag suggestions."""
    suggested_tags: List[TagSuggestion] = Field(
        description="Tag suggestions for the paragraph",
        min_length=1,
        max_length=10
    )


class OllamaTagSuggester:
    """Handles Ollama integration for automatic tag suggestions using Pydantic."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the Ollama tag suggester.
        
        Args:
            model_name: The Ollama model to use for suggestions. If None, will auto-detect.
        """
        self.client = ollama  # Set client first
        self.model_name = model_name or self._auto_detect_model()
    
    def _auto_detect_model(self) -> str:
        """Auto-detect the best available model."""
        try:
            models_response = self.client.list()
            
            # Handle new response format with model objects
            if hasattr(models_response, 'models'):
                models = models_response.models
            else:
                models = models_response.get('models', [])
            
            # Extract model names from the response
            model_names = []
            for model in models:
                if hasattr(model, 'model'):
                    # New format: model object with .model attribute
                    model_names.append(model.model)
                elif isinstance(model, dict):
                    # Old format: dictionary with 'name' key
                    model_names.append(model.get('name', ''))
                elif isinstance(model, str):
                    # Simple string format
                    model_names.append(model)
            
            # Preferred model order (updated to prioritize available models)
            preferred_models = [
                'llama3.2:latest', 'llama3.2', 'llama3:latest', 'llama3',
                'gemma2:latest', 'gemma2', 'gemma3:latest', 'gemma3',
                'gemma3:1b', 'gemma2:2b', 'mistral:latest', 'mistral'
            ]
            
            # Find the first preferred model that's available
            for preferred in preferred_models:
                if preferred in model_names:
                    return preferred
            
            # If no preferred models, return the first available model
            if model_names:
                return model_names[0]
            
            return 'llama3.2:latest'  # Fallback
            
        except Exception as e:
            # Don't show error if running outside Streamlit context
            try:
                import streamlit as st
                st.error(f"Error detecting models: {e}")
            except:
                pass
            return 'llama3.2:latest'  # Fallback
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available and the model is accessible.
        
        Returns:
            bool: True if Ollama is available and model is accessible
        """
        try:
            # Try to list available models
            models_response = self.client.list()
            
            # Handle new response format
            if hasattr(models_response, 'models'):
                models = models_response.models
            else:
                models = models_response.get('models', [])
            
            # Extract model names
            model_names = []
            for model in models:
                if hasattr(model, 'model'):
                    model_names.append(model.model)
                elif isinstance(model, dict):
                    model_names.append(model.get('name', ''))
                elif isinstance(model, str):
                    model_names.append(model)
            
            return self.model_name in model_names
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of available model names
        """
        try:
            models_response = self.client.list()
            
            # Handle new response format
            if hasattr(models_response, 'models'):
                models = models_response.models
            else:
                models = models_response.get('models', [])
            
            # Extract model names
            model_names = []
            for model in models:
                if hasattr(model, 'model'):
                    model_names.append(model.model)
                elif isinstance(model, dict):
                    model_names.append(model.get('name', ''))
                elif isinstance(model, str):
                    model_names.append(model)
            
            return model_names
        except Exception:
            return []
    
    def suggest_tags(self, paragraph_content: str, tag_hierarchy: List[Dict[str, Any]], 
                    existing_tags: List[str] = None, custom_prompt: str = None, 
                    num_suggestions: int = 2) -> Optional[List[Dict[str, str]]]:
        """
        Get tag suggestions for a paragraph using Ollama with Pydantic structured output.
        
        Args:
            paragraph_content: The paragraph text to analyze
            tag_hierarchy: List of all available tags with hierarchy
            existing_tags: Tags already applied to this paragraph
            custom_prompt: Custom prompt template to use
            num_suggestions: Number of suggestions to generate (1-10)
            
        Returns:
            List of suggested tags with reasoning and confidence, or None if error
        """
        if existing_tags is None:
            existing_tags = []
        
        # Clamp num_suggestions to valid range
        num_suggestions = max(1, min(10, num_suggestions))
        
        try:
            # Create a structured representation of the tag hierarchy
            tag_structure = self._format_tag_hierarchy(tag_hierarchy)
            
            # Create the prompt
            if custom_prompt:
                prompt = self._create_custom_prompt(
                    custom_prompt, paragraph_content, tag_structure, existing_tags, num_suggestions
                )
            else:
                prompt = self._create_tag_suggestion_prompt(
                    paragraph_content, tag_structure, existing_tags, num_suggestions
                )
            
            # Update Pydantic model constraints for variable number of suggestions
            TagSuggestionsResponse.model_fields['suggested_tags'].metadata[0] = Field(
                description="Tag suggestions for the paragraph",
                min_length=1,
                max_length=num_suggestions
            )
            
            # Use Pydantic model to generate JSON schema
            response_schema = TagSuggestionsResponse.model_json_schema()
            
            # Get model parameters from Streamlit session state if available
            temperature = 0.3  # Default
            top_p = 0.9  # Default
            
            # Try to get parameters from Streamlit session state
            try:
                import streamlit as st
                temperature = st.session_state.get('ai_temperature', 0.3)
                top_p = st.session_state.get('ai_top_p', 0.9)
            except:
                pass  # Use defaults if Streamlit not available
            
            # Make the request to Ollama with structured output
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                format=response_schema,
                stream=False,
                options={
                    'temperature': temperature,
                    'top_p': top_p,
                }
            )
            
            # Parse the response using Pydantic
            response_text = response['response']
            
            # Clean up the response text if needed
            response_text = response_text.strip()
            if not response_text.startswith('{'):
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                if start_idx != -1:
                    response_text = response_text[start_idx:]
            
            # Parse JSON and validate with Pydantic
            parsed_data = json.loads(response_text)
            validated_response = TagSuggestionsResponse.model_validate(parsed_data)
            
            # Convert to the expected format
            suggestions = []
            for suggestion in validated_response.suggested_tags:
                suggestions.append({
                    'tag_name': suggestion.tag_name,
                    'confidence': suggestion.confidence,
                    'reasoning': suggestion.reasoning
                })
            
            return suggestions
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing AI response as JSON: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Error getting tag suggestions: {str(e)}")
            return None
    
    def _format_tag_hierarchy(self, tag_hierarchy: List[Dict[str, Any]]) -> str:
        """Format tag hierarchy for the prompt."""
        def format_tag(tag, level=0):
            indent = "  " * level
            result = f"{indent}- {tag['name']}"
            if tag.get('description'):
                result += f" ({tag['description']})"
            result += "\n"
            
            # Add children
            children = [t for t in tag_hierarchy if t.get('parent_tag_id') == tag['id']]
            for child in children:
                result += format_tag(child, level + 1)
            
            return result
        
        # Get root tags (those without parents)
        root_tags = [tag for tag in tag_hierarchy if tag.get('parent_tag_id') is None]
        
        formatted = "Available Tags:\n"
        for root_tag in root_tags:
            formatted += format_tag(root_tag)
        
        return formatted
    
    def _create_tag_suggestion_prompt(self, paragraph_content: str, 
                                    tag_structure: str, existing_tags: List[str],
                                    num_suggestions: int) -> str:
        """Create the default prompt for tag suggestions with reasoning-first approach."""
        existing_tags_str = ", ".join(existing_tags) if existing_tags else "None"
        
        return f"""You are an expert at analyzing religious conference talks and suggesting appropriate tags.

{tag_structure}

Paragraph to analyze:
"{paragraph_content}"

Currently applied tags: {existing_tags_str}

Instructions:
1. First, carefully analyze the paragraph content to understand its main themes, concepts, and doctrines
2. For each potential tag, think through the reasoning BEFORE deciding to suggest it
3. Suggest exactly {num_suggestions} tags that would be most appropriate for this paragraph
4. Only suggest tags that exist EXACTLY as written in the provided tag hierarchy
5. Do not suggest tags that are already applied to this paragraph
6. For each suggestion, provide the reasoning first, then the tag name and confidence level
7. Focus on the main themes, concepts, or doctrines discussed in the paragraph
8. Consider both specific topics and broader theological themes
9. Confidence levels: "high" (very certain), "medium" (reasonably certain), "low" (possible but uncertain)

Structure your response as JSON with exactly {num_suggestions} tag suggestions. Each suggestion must include:
- reasoning: A detailed explanation of why this tag fits the paragraph content
- tag_name: The exact tag name from the available tags (must match exactly)
- confidence: Either "high", "medium", or "low"

Think step by step: analyze the content, consider the reasoning for each potential tag, then provide your {num_suggestions} best suggestions."""

    def _create_custom_prompt(self, custom_prompt: str, paragraph_content: str, 
                            tag_structure: str, existing_tags: List[str],
                            num_suggestions: int) -> str:
        """Create a custom prompt using the user's template."""
        existing_tags_str = ", ".join(existing_tags) if existing_tags else "None"
        
        # Replace placeholders in the custom prompt
        formatted_prompt = custom_prompt.format(
            tag_structure=tag_structure,
            paragraph_content=paragraph_content,
            existing_tags=existing_tags_str,
            num_suggestions=num_suggestions
        )
        
        return formatted_prompt


def create_ollama_tag_suggester(model_name: str = None) -> OllamaTagSuggester:
    """
    Factory function to create an OllamaTagSuggester instance.
    
    Args:
        model_name: Optional model name override. If None, will auto-detect from session state or available models.
        
    Returns:
        OllamaTagSuggester instance
    """
    if model_name is None:
        # Try to get from session state or auto-detect
        model_name = st.session_state.get('ollama_model')
    
    return OllamaTagSuggester(model_name)
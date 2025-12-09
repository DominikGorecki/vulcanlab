"""
CLI for generating and managing augmented RAG prompts.

This script generates augmented prompts from database queries and allows
users to display, copy to clipboard, or send to an LLM.

Usage:
    venv\\Scripts\\python -m vulcanlab.augmentation.augment_cli --query-id 1 [--top-n 5]

Examples:
    # Generate prompt for query ID 1 with default 5 contexts
    venv\\Scripts\\python -m vulcanlab.augmentation.augment_cli --query-id 1

    # Generate prompt with 10 contexts
    venv\\Scripts\\python -m vulcanlab.augmentation.augment_cli --query-id 1 --top-n 10

Options:
    --query-id    Query ID from database (required)
    --top-n       Number of top contexts to include (default: 5)
"""

import argparse
import sys

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from .augment import generate_augmented_prompt
from ..ai.llm_factory import create_langchain_chat
from ..ai.config import ModelTier


def display_prompt(prompt: str) -> None:
    """Display the prompt to the user with visual separators."""
    print("\n" + "=" * 80)
    print("GENERATED PROMPT")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    print()


def copy_to_clipboard(prompt: str) -> None:
    """Copy the prompt to clipboard."""
    if not CLIPBOARD_AVAILABLE:
        print("\n❌ Clipboard functionality not available. Install pyperclip: pip install pyperclip")
        return
    
    try:
        pyperclip.copy(prompt)
        print("\n✅ Prompt copied to clipboard!")
    except Exception as e:
        print(f"\n❌ Failed to copy to clipboard: {e}")


def send_to_llm(prompt: str) -> None:
    """Send the prompt to LLM and display response."""
    print("\n🤖 Sending to LLM (FULL model with search enabled)...")
    print("This may take a moment...\n")
    
    try:
        # Create LangChain chat with FULL tier and search enabled
        stack = create_langchain_chat(
            tier=ModelTier.FULL,
            search=True,
            temperature=0.2
        )
        
        # Send prompt and get response
        response = stack.chat.invoke(prompt)
        
        # Display response
        print("\n" + "=" * 80)
        print("LLM RESPONSE")
        print("=" * 80)
        print(response.content)
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ Error sending to LLM: {e}")
        print("Make sure your API keys are configured in .env file.")


def interactive_menu(prompt: str) -> None:
    """
    Display interactive menu for user actions.
    
    Args:
        prompt: The generated prompt string
    """
    while True:
        print("\nWhat would you like to do?")
        print("  [send]  - Send prompt to LLM (FULL model with search)")
        print("  [copy]  - Copy prompt to clipboard")
        print("  [exit]  - Exit the program")
        
        choice = input("\nAction [send/copy/exit]: ").strip().lower()
        
        if choice == "send":
            send_to_llm(prompt)
            # After sending, show menu again
            continue
        elif choice == "copy":
            copy_to_clipboard(prompt)
            # After copying, show menu again
            continue
        elif choice == "exit":
            print("\n👋 Goodbye!")
            break
        else:
            print(f"\n❌ Invalid choice: '{choice}'. Please choose 'send', 'copy', or 'exit'.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate augmented RAG prompts from database queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate prompt for query ID 1 with default 5 contexts
  python -m vulcanlab.augmentation.augment_cli --query-id 1

  # Generate prompt with 10 contexts
  python -m vulcanlab.augmentation.augment_cli --query-id 1 --top-n 10
        """
    )
    
    parser.add_argument(
        "--query-id",
        type=int,
        required=True,
        help="Query ID from database"
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top contexts to include (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Generate prompt
    try:
        print(f"\n🔍 Generating prompt for query ID {args.query_id} with top {args.top_n} contexts...")
        prompt = generate_augmented_prompt(args.query_id, args.top_n)
        
        # Display the prompt
        display_prompt(prompt)
        
        # Show interactive menu
        interactive_menu(prompt)
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


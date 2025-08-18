"""
Tests for CLI functionality.
"""

from unittest.mock import patch

import pytest

from pyrattler_recipe_autogen.cli import main


def test_main_default_args():
    """Test main function with default arguments."""
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        main([])

        # Verify generate_recipe was called with default paths
        mock_generate.assert_called_once()
        args = mock_generate.call_args[0]
        assert str(args[0]) == "pyproject.toml"
        assert str(args[1]) == "recipe/recipe.yaml"
        assert args[2] is False  # overwrite parameter


def test_main_custom_args():
    """Test main function with custom arguments."""
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        main(["-i", "custom.toml", "-o", "output.yaml", "--overwrite"])

        # Verify generate_recipe was called with custom paths
        mock_generate.assert_called_once()
        args = mock_generate.call_args[0]
        assert str(args[0]) == "custom.toml"
        assert str(args[1]) == "output.yaml"
        assert args[2] is True  # overwrite parameter


def test_main_file_not_found():
    """Test main function with FileNotFoundError."""
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        mock_generate.side_effect = FileNotFoundError("pyproject.toml not found")

        with pytest.raises(SystemExit) as exc_info:
            main([])

        # Should exit with the error message
        assert exc_info.type is SystemExit
        assert str(exc_info.value) == "pyproject.toml not found"


def test_main_generic_error():
    """Test main function with generic exception."""
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        mock_generate.side_effect = ValueError("Invalid configuration")

        with pytest.raises(SystemExit) as exc_info:
            main([])

        # Should exit with prefixed error message
        assert exc_info.type is SystemExit
        assert str(exc_info.value) == "Error generating recipe: Invalid configuration"


def test_main_expanduser():
    """Test that paths are expanded with expanduser."""
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        main(["-i", "~/pyproject.toml", "-o", "~/recipe.yaml"])

        # Verify paths were expanded
        mock_generate.assert_called_once()
        args = mock_generate.call_args[0]
        # The exact expanded path depends on the environment, but should not contain ~
        assert "~" not in str(args[0])
        assert "~" not in str(args[1])


def test_main_help():
    """Test that help text is properly configured."""
    with patch("sys.argv", ["pyrattler-recipe-autogen", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Help should exit with code 0
        assert exc_info.value.code == 0


def test_argument_parser():
    """Test argument parser configuration."""
    # This indirectly tests the argument parser by calling main
    with patch("pyrattler_recipe_autogen.cli.generate_recipe") as mock_generate:
        # Test long form arguments
        main(["--input", "test.toml", "--output", "test.yaml", "--overwrite"])

        mock_generate.assert_called_once()
        args = mock_generate.call_args[0]
        assert str(args[0]) == "test.toml"
        assert str(args[1]) == "test.yaml"
        assert args[2] is True  # overwrite parameter


if __name__ == "__main__":
    pytest.main([__file__])

#!/usr/bin/env python3
"""
Legacy generate_site.py - now imports from new modular structure.
This file is kept for backwards compatibility.
"""

from wardrobe.core.generator import generate_wardrobe_sites


def main():
    """Main function using new modular structure."""
    generate_wardrobe_sites()


if __name__ == "__main__":
    main()
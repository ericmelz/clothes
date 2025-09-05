# TODO incorporate server and deploy functionality here
"""Command-line interface for wardrobe management."""

from pathlib import Path
import argparse
import os
import sys

from .core.generator import WardrobeGenerator, generate_wardrobe_sites


def main():
    """Main CLI entry point."""
    data_path = Path(os.getenv("HOME")) / "Data" / "wardrobe"
    code_path = Path(os.getenv("HOME")) / "Data" / "code"
    source_data_path_str = str(data_path / "source_data")

    auth_path =  data_path / "auth"
    output_path_str = str(data_path / "output")

    creds_path_str = str(auth_path / "credentials.json")
    readwrite_token_path_str = str(auth_path / "token.json")
    readonly_token_path_str = str(auth_path / "token_readonly.json")

    site_template_path_str = str(code_path / "clothes" / "src" / "site_template")

    parser = argparse.ArgumentParser(description="Wardrobe management system")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command - all people
    gen_parser = subparsers.add_parser('generate', help='Generate wardrobe site')
    gen_parser.add_argument('--people', nargs='+', default=['eric', 'randi'],
                            help='People to generate sites for')
    gen_parser.add_argument('--source', default=source_data_path_str,
                            help='Source data directory')
    gen_parser.add_argument('--output', default=output_path_str,
                            help='Output directory')
    gen_parser.add_argument('--template', default=site_template_path_str,
                            help='Site template directory')
    gen_parser.add_argument('--skip-images', action='store_true',
                            help='Skip image processing')
    gen_parser.add_argument('--readwrite-token', default=readwrite_token_path_str,
                            help='Read/write token path')
    gen_parser.add_argument('--readonly-token', default=readonly_token_path_str,
                            help='Read-only token path')
    gen_parser.add_argument('--creds', default=creds_path_str, help='Credentials path')

    # Single person generate
    single_parser = subparsers.add_parser('generate-single', help='Generate site for single person')
    single_parser.add_argument('person', help='Person name')
    single_parser.add_argument('--source', default=source_data_path_str, help='Source data directory')
    single_parser.add_argument('--output', default=output_path_str, help='Output directory')
    single_parser.add_argument('--template', default=site_template_path_str, help='Template directory')
    single_parser.add_argument('--sheet', help='Google Sheets name')
    single_parser.add_argument('--skip-images', action='store_true', help='Skip image processing')
    single_parser.add_argument('--readwrite-token', default=readwrite_token_path_str,
                               help='Read/write token path')
    single_parser.add_argument('--readonly-token', default=readonly_token_path_str,
                               help='Read-only token path')
    single_parser.add_argument('--creds', default=creds_path_str, help='Credentials path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'generate':
            generate_wardrobe_sites(
                people=args.people,
                output_base=args.output,
                source_base=args.source,
                site_template_dir=args.template,
                skip_image_processing=args.skip_images,
                readwrite_token_path=readwrite_token_path_str,
                readonly_token_path=readonly_token_path_str,
                creds_path=creds_path_str,
            )
        elif args.command == 'generate-single':
            source_dir = args.source or f'source_data/{args.person}s-clothes'
            output_dir = args.output or f'output/{args.person}s-clothes'
            sheet_name = args.sheet or f'{args.person}-wardrobe'

            generator = WardrobeGenerator(
                source_dir=source_dir,
                output_dir=output_dir,
                site_template_dir=args.template,
                skip_image_processing=args.skip_images,
                readwrite_token_path=readwrite_token_path_str,
                readonly_token_path=readonly_token_path_str,
                creds_path=creds_path_str,
                metadata_sheetname=sheet_name
            )
            generator.generate()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

"""Command-line interface for wardrobe management."""

import argparse
import sys

from .core.generator import WardrobeGenerator, generate_wardrobe_sites


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Wardrobe management system")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate wardrobe site')
    gen_parser.add_argument('--people', nargs='+', default=['eric', 'randi'],
                           help='People to generate sites for')
    gen_parser.add_argument('--output', default='output',
                           help='Output directory')
    gen_parser.add_argument('--template', default='site_template',
                           help='Site template directory')
    gen_parser.add_argument('--skip-images', action='store_true',
                           help='Skip image processing')
    
    # Single person generate
    single_parser = subparsers.add_parser('generate-single', help='Generate site for single person')
    single_parser.add_argument('person', help='Person name')
    single_parser.add_argument('--source', help='Source directory')
    single_parser.add_argument('--output', help='Output directory')
    single_parser.add_argument('--template', default='site_template', help='Template directory')
    single_parser.add_argument('--sheet', help='Google Sheets name')
    single_parser.add_argument('--skip-images', action='store_true', help='Skip image processing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'generate':
            generate_wardrobe_sites(
                people=args.people,
                output_base=args.output,
                site_template_dir=args.template
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
                metadata_sheetname=sheet_name
            )
            generator.generate()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
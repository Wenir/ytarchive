import logging
import asyncio
import argparse
import yaml
from pathlib import Path
from dataclasses import asdict

from ytarchive_lib.config import load_config
from ytarchive_lib.data_manager import DataManager, Warning, SrcItem


async def list_warnings(args):
    """List all warnings with their associated items"""
    config = load_config()

    async with await DataManager.create(config) as data_manager:
        state_filter = Warning.State.NEW if args.new else None
        warnings = []

        async for warning, src_item in data_manager.get_warnings(state_filter):
            warnings.append((warning, src_item))

        if not warnings:
            logging.info("No warnings found")
            return

        logging.info(f"Found {len(warnings)} warnings")

        for warning, src_item in warnings:
            print(f"\n{'='*80}")
            print(f"Provider: {warning.provider}")
            print(f"ID: {warning.id}")
            print(f"Warning ID: {warning.warning_id}")
            print(f"Warning State: {warning.state}")
            print(f"Message: {warning.message}")

            if src_item:
                print(f"\nItem State: {src_item.state}")
                print(f"Title: {src_item.title}")
                print(f"Channel: {src_item.channel}")
                print(f"Duration: {src_item.duration}s")
                print(f"URL: {src_item.url}")
            else:
                print("\n[No associated src_item found]")


async def export_warnings(args):
    """Export warnings to YAML file"""
    config = load_config()

    async with await DataManager.create(config) as data_manager:
        state_filter = Warning.State.NEW if args.new else None
        warnings_data = []

        async for warning, src_item in data_manager.get_warnings(state_filter):
            item_data = {
                'id': warning.id,
                'provider': warning.provider,
                'warning_id': warning.warning_id,
                'warning_state': str(warning.state),
                'message': warning.message,
                'clear': False,  # Default to False, user will set to True to clear
            }

            if src_item:
                item_data['item_state'] = str(src_item.state)
                item_data['title'] = src_item.title
                item_data['channel'] = src_item.channel
                item_data['duration'] = src_item.duration
                item_data['url'] = src_item.url
                item_data['priority'] = src_item.priority

            warnings_data.append(item_data)

        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            yaml.dump(warnings_data, f, default_flow_style=False, allow_unicode=True)

        logging.info(f"Exported {len(warnings_data)} warnings to {output_path}")
        print(f"\nExported {len(warnings_data)} warnings to {output_path}")
        print(f"Edit the file and set 'clear: true' for warnings you want to clear,")
        print(f"then run: warnings clear {output_path}")


async def clear_warnings(args):
    """Clear warnings marked in YAML file"""
    config = load_config()
    input_path = Path(args.input)

    if not input_path.exists():
        logging.error(f"File not found: {input_path}")
        print(f"Error: File not found: {input_path}")
        return

    with open(input_path, 'r') as f:
        warnings_data = yaml.safe_load(f)

    if not warnings_data:
        logging.info("No warnings in file")
        print("No warnings in file")
        return

    # Filter warnings marked for clearing
    to_clear = [w for w in warnings_data if w.get('clear', False)]

    if not to_clear:
        logging.info("No warnings marked for clearing (clear: true)")
        print("No warnings marked for clearing. Set 'clear: true' in the YAML file.")
        return

    logging.info(f"Found {len(to_clear)} warnings marked for clearing")
    print(f"\nFound {len(to_clear)} warnings marked for clearing:")

    async with await DataManager.create(config) as data_manager:
        cleared_count = 0
        for warning in to_clear:
            provider = warning['provider']
            vid_id = warning['id']
            title = warning.get('title', 'N/A')

            print(f"  - Clearing: {provider}:{vid_id} - {title}")
            logging.info(f"Clearing warning: {provider}:{vid_id}")

            await data_manager.clear_warning(provider, vid_id)
            cleared_count += 1

        print(f"\nSuccessfully cleared {cleared_count} warnings")
        logging.info(f"Successfully cleared {cleared_count} warnings")


def main():
    parser = argparse.ArgumentParser(
        description='Manage warnings in YTArchive database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all warnings
  warnings list

  # List only NEW warnings
  warnings list --new

  # Export warnings to YAML
  warnings export warnings.yml

  # Export only NEW warnings
  warnings export warnings.yml --new

  # Clear warnings marked in YAML
  warnings clear warnings.yml
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True

    # List command
    list_parser = subparsers.add_parser('list', help='List all warnings')
    list_parser.add_argument(
        '--new',
        help='List only new warnings',
        action='store_true',
    )
    list_parser.set_defaults(func=list_warnings)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export warnings to YAML file')
    export_parser.add_argument('output', help='Output YAML file path')
    export_parser.add_argument(
        '--new',
        help='Output only new warnings',
        action='store_true',
    )
    export_parser.set_defaults(func=export_warnings)

    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear warnings marked in YAML file')
    clear_parser.add_argument('input', help='Input YAML file with marked warnings')
    clear_parser.set_defaults(func=clear_warnings)

    args = parser.parse_args()
    asyncio.run(args.func(args))

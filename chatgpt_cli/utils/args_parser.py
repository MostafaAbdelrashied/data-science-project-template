import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="OpenAI Chat Interface")
    parser.add_argument(
        "-s",
        "--stream",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Stream the conversation in real-time",
    )
    parser.add_argument(
        "-r",
        "--read_file",
        type=str,
        help="Path to a text file to include at the start of the chat",
    )
    return parser.parse_args()

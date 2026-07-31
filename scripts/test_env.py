import os

from dotenv import load_dotenv


def main() -> None:
    """Report configuration presence without printing credential values."""
    load_dotenv()

    for variable in ("GROQ_API_KEY", "RAPIDAPI_KEY"):
        status = "yes" if os.getenv(variable) else "no"
        print(f"{variable} configured: {status}")


if __name__ == "__main__":
    main()

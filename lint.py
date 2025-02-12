# lint.py
import typer
import subprocess

app = typer.Typer()


@app.command()
def lint():
    # Run Black, etc.
    subprocess.run(["black", "."], check=True)
    typer.echo("Linting complete!")


if __name__ == "__main__":
    app()


import os
import base64
import uuid
from datetime import datetime, timezone

import aiohttp
import discord
from discord import app_commands

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

REPO = "applefruit1/svg-link-generator"
BRANCH = "main"
API = f"https://api.github.com/repos/{REPO}/contents"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def github_request(session, method, url, **kwargs):
    async with session.request(method, url, **kwargs) as response:
        data = await response.json()

        if response.status not in (200, 201):
            raise RuntimeError(
                f"GitHub API error ({response.status}): "
                f"{data.get('message', 'Unknown error')}"
            )

        return data


@tree.command(name="link", description="Generate SVG links")
@app_commands.describe(
    amount="Number of links to generate (1–10)"
)
@app_commands.guild_only()
async def link(
    interaction: discord.Interaction,
    amount: app_commands.Range[int, 1, 10]
):
    await interaction.response.defer(
        thinking=True, ephemeral=True
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        async with aiohttp.ClientSession(
            headers=headers
        ) as session:
            source = await github_request(
                session,
                "GET",
                f"{API}/source.svg",
                params={"ref": BRANCH},
            )

            svg_bytes = base64.b64decode(source["content"])

            if b"<svg" not in svg_bytes.lower():
                raise RuntimeError(
                    "source.svg does not contain SVG markup."
                )

            links = []

            for _ in range(amount):
                stamp = datetime.now(
                    timezone.utc
                ).strftime("%Y%m%d%H%M%S")

                filename = (
                    f"{stamp}_{uuid.uuid4().hex[:16]}.svg"
                )
                path = f"generated/{filename}"

                payload = {
                    "message": f"Generate SVG {filename}",
                    "content": base64.b64encode(
                        svg_bytes
                    ).decode("ascii"),
                    "branch": BRANCH,
                }

                await github_request(
                    session,
                    "PUT",
                    f"{API}/{path}",
                    json=payload,
                )

                url = (
                    f"https://cdn.jsdelivr.net/gh/"
                    f"{REPO}@{BRANCH}/{path}"
                )
                links.append(url)

        message = "\n".join(
            f"{i}. <{url}>"
            for i, url in enumerate(links, 1)
        )

        await interaction.followup.send(
            f"**Generated {len(links)} SVG links:**\n"
            f"{message}",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    except Exception as exc:
        print(f"Generation failed: {exc}")
        await interaction.followup.send(
            "Couldn't generate the links. Check the "
            "deployment logs and GitHub token permissions.",
            ephemeral=True,
        )


@client.event
async def on_ready():
    synced = await tree.sync()
    print(f"Logged in as {client.user}")
    print(f"Synced {len(synced)} global slash commands.")
    print("The /link command is ready.")


client.run(DISCORD_TOKEN)

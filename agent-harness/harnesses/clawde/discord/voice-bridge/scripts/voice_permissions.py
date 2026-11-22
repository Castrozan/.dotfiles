def matching_grant(specification, host, listener_user_id, guild_id):
    return all(
        (
            specification["ownerHost"] == host,
            int(specification["listenerUserId"]) == listener_user_id,
            int(specification["guildId"]) == guild_id,
        )
    )


def unique_grants(specifications):
    identifiers = set()
    selected = []
    for specification in specifications:
        keys = {("name", specification["name"]), ("token", specification["tokenFile"])}
        if keys & identifiers:
            continue
        identifiers.update(keys)
        selected.append(specification)
    return selected


def identity_specifications(specifications, host, listener_user_id, guild_id):
    if not 1 <= len(specifications) <= 8:
        raise ValueError("voice_identity_count_out_of_bounds")
    return unique_grants(
        [
            specification
            for specification in specifications
            if matching_grant(specification, host, listener_user_id, guild_id)
        ]
    )


def member_refusal(channel, member):
    permissions = channel.permissions_for(member)
    if not all((permissions.view_channel, permissions.connect, permissions.speak)):
        return "missing_voice_permissions"
    return server_voice_refusal(member)


def server_voice_refusal(member):
    if member.voice is None:
        return None
    if any((member.voice.mute, member.voice.deaf)):
        return "bot_server_muted_or_deafened"
    return None


def channel_capacity_refusal(channel):
    kind = getattr(channel, "type", None)
    if kind is not None and str(kind) != "voice":
        return "unsupported_voice_channel"
    if channel.user_limit and len(channel.voice_states) >= channel.user_limit:
        return "voice_channel_full"
    return None


def channel_refusal(channel, member):
    return member_refusal(channel, member) or channel_capacity_refusal(channel)


def guild_listener_channel(guild, listener_user_id):
    return next(
        (
            channel
            for channel in guild.voice_channels
            if listener_user_id in channel.voice_states
        ),
        None,
    )


def identity_guild(identity, guild_id):
    if identity.error:
        return None, identity.error
    if not identity.client.is_ready():
        return None, "identity_not_ready"
    guild = identity.client.get_guild(guild_id)
    if guild is None or guild.me is None:
        return None, "bot_not_in_allowed_guild"
    return guild, None


def occupancy_refusal(identity, member, bridge_owned_voice_state):
    if getattr(member.voice, "channel", None) is None:
        return None
    if identity.lease is not None:
        return "owned_call"
    return None if bridge_owned_voice_state else "bot_voice_connection_in_use"


def ready_identity(identity):
    return identity.error is None and identity.client.is_ready()


def listener_absent(identities, listener_user_id, guild_id):
    guilds = (identity_guild(identity, guild_id)[0] for identity in identities)
    visible_guilds = [guild for guild in guilds if guild is not None]
    return bool(visible_guilds) and not any(
        guild_listener_channel(guild, listener_user_id) for guild in visible_guilds
    )


def join_refusal(identities, listener_user_id, guild_id):
    if not any(ready_identity(identity) for identity in identities):
        return "bridge_not_ready"
    if listener_absent(identities, listener_user_id, guild_id):
        return "listener_not_in_allowed_voice_channel"
    return "no_eligible_available_bot_for_listener"

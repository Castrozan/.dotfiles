{ isDarwin }:
{
  userDataDirectoryRelativeToHome =
    if isDarwin then "Library/Application Support/Vivaldi" else ".config/vivaldi";
}

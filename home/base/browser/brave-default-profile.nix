{ isDarwin }:
{
  userDataDirectoryRelativeToHome =
    if isDarwin then
      "Library/Application Support/BraveSoftware/Brave-Browser"
    else
      ".config/BraveSoftware/Brave-Browser";
}

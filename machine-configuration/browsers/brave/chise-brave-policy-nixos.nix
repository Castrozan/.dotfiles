_: {
  environment.etc."brave/policies/managed/dotfiles-managed-policies.json".text = builtins.toJSON {
    PasswordManagerEnabled = false;
    DefaultSearchProviderEnabled = true;
    DefaultSearchProviderName = "DuckDuckGo";
    DefaultSearchProviderKeyword = ":d";
    DefaultSearchProviderSearchURL = "https://duckduckgo.com/?q={searchTerms}&t=brave";
    DefaultSearchProviderSuggestURL = "https://ac.duckduckgo.com/ac/?q={searchTerms}&type=list";
    DefaultSearchProviderIconURL = "https://duckduckgo.com/favicon.ico";
  };
}

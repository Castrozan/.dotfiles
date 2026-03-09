function __source_bash_aliases_into_fish
  bass source ~/.dotfiles/home/modules/terminal/shell/aliases.sh

  set -l bash_alias_definition_field_delimiter (printf '\t')
  set -l bash_alias_definitions (
    command bash -c '
      source "$HOME/.dotfiles/home/modules/terminal/shell/aliases.sh" >/dev/null 2>&1

      while IFS= read -r bash_alias_definition; do
        bash_alias_name=${bash_alias_definition#alias }
        bash_alias_name=${bash_alias_name%%=*}
        bash_alias_body=${bash_alias_definition#*=}
        printf "%s\t%s\n" "$bash_alias_name" "$bash_alias_body"
      done < <(alias -p)
    '
  )

  for bash_alias_definition in $bash_alias_definitions
    set -l parsed_bash_alias_definition (
      string split -m 1 "$bash_alias_definition_field_delimiter" -- "$bash_alias_definition"
    )

    if test (count $parsed_bash_alias_definition) -ne 2
      continue
    end

    set -l quoted_bash_alias_body "$parsed_bash_alias_definition[2]"
    set -l quoted_bash_alias_body_length (string length -- "$quoted_bash_alias_body")

    if test $quoted_bash_alias_body_length -lt 2
      continue
    end

    set -l unquoted_bash_alias_body (
      string sub -s 2 -l (math "$quoted_bash_alias_body_length - 2") -- "$quoted_bash_alias_body"
    )
    alias $parsed_bash_alias_definition[1] "$unquoted_bash_alias_body"
  end

  alias source-shell 'source ~/.dotfiles/home/modules/terminal/shell/fish/config.fish'
end

__source_bash_aliases_into_fish

set -l privateAliasesFile "$HOME/.dotfiles/private-config/shell/aliases.sh"

if not test -f $privateAliasesFile
    return
end

for line in (cat $privateAliasesFile)
    set -l aliasMatch (string match -r '^\\s*alias\\s+(\\S+)=(.*)' $line)
    if test (count $aliasMatch) -eq 3
        set -l aliasName $aliasMatch[2]
        set -l aliasBodyWithQuotes $aliasMatch[3]
        set -l aliasBody (string replace -r "^['\"](.*)['\"]\$" '$1' $aliasBodyWithQuotes)
        alias $aliasName $aliasBody
        continue
    end

    set -l exportMatch (string match -r '^\\s*export\\s+(\\w+)=(.*)' $line)
    if test (count $exportMatch) -eq 3
        set -l exportName $exportMatch[2]
        set -l exportValueWithQuotes $exportMatch[3]
        set -l exportValue (string replace -r "^['\"](.*)['\"]\$" '$1' $exportValueWithQuotes)
        set -gx $exportName (eval echo $exportValue)
    end
end

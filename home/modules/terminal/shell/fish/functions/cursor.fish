# Functions for cursor - allows parameters and runs detached
function cursor
    command cursor $argv > /dev/null 2>&1 &
    disown
end

# Function for cu - defaults to current directory if no params, otherwise passes all params
function cu
    if count $argv > /dev/null
        cursor $argv
    else
        cursor .
    end
end

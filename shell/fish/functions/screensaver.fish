# Function for cbonsai
function bonsai
    cbonsai $argv
end

# Function for pipes.sh
function pipes
    pipes.sh $argv
end

# Function for pipes as screensaver
function pipes_screensaver
    pipes
end

# Function for cbonsai as screensaver
function bonsai_screensaver
    bonsai -l -i -b 1 -c mWmW,wMwM,mMw -M 2 --life 35
end

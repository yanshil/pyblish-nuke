# Adds custom build arguments
parser.add_argument("--symlink", action="store_true", help="Make symbolic link")
parser.add_argument("--current", action="store_true", help='Build "current" folder')
parser.add_argument(
    "--pc", action="store_true", help="upload pipline config to shotgun"
)

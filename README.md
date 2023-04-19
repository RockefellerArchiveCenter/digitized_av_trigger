# digitized_av_notifications
Handles notifications for validation and packaging of incoming digitized audiovisual assets.

[![Build Status](https://app.travis-ci.com/RockefellerArchiveCenter/digitized_av_notifications.svg?branch=base)](https://app.travis-ci.com/RockefellerArchiveCenter/digitized_av_notifications)

## Getting Started

With [git](https://git-scm.com/) installed, pull down the source code and move into the newly created directory:

```
git clone https://github.com/RockefellerArchiveCenter/digitized_av_notifications.git
cd digitized_av_notifications
```

With the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) and [Docker](https://www.docker.com/community-edition) installed, build the application:

```
sam build --hook-name terraform --beta-features aws_lambda_function.handle_digitized_av_notifications
```

Then, invoke the function using one of the fixtures:

```
sam local invoke --hook-name terraform --beta-features handle_digitized_av_notifications -e fixtures/failure_message.json
```

## Usage

This repository is intended to be deployed as a Lambda script in AWS infrastructure.

## License

This code is released under the MIT License.

## Contributing

This is an open source project and we welcome contributions! If you want to fix a bug, or have an idea of how to enhance the application, the process looks like this:

1. File an issue in this repository. This will provide a location to discuss proposed implementations of fixes or enhancements, and can then be tied to a subsequent pull request.
2. If you have an idea of how to fix the bug (or make the improvements), fork the repository and work in your own branch. When you are done, push the branch back to this repository and set up a pull request. Automated unit tests are run on all pull requests. Any new code should have unit test coverage, documentation (if necessary), and should conform to the Python PEP8 style guidelines.
3. After some back and forth between you and core committers (or individuals who have privileges to commit to the base branch of this repository), your code will probably be merged, perhaps with some minor changes.

This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.

## Tests

New code should have unit tests. Tests can be run using [tox](https://tox.readthedocs.io/).

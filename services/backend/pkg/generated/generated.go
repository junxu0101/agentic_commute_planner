package generated

import (
	"github.com/99designs/gqlgen/graphql"
)

type Config struct {
	Resolvers interface{}
}

type ResolverRoot interface {
	Query() interface{}
	Mutation() interface{}
}

func NewExecutableSchema(cfg Config) graphql.ExecutableSchema {
	return &executableSchema{
		resolvers: cfg.Resolvers,
	}
}

type executableSchema struct {
	resolvers interface{}
}

func (e *executableSchema) Schema() *graphql.Schema {
	return parsedSchema
}

func (e *executableSchema) Complexity(typeName, field string, childComplexity int, rawArgs map[string]interface{}) (int, bool) {
	return 0, false
}

var parsedSchema = &graphql.Schema{}
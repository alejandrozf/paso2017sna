(defproject get_tweets "0.1.0-SNAPSHOT"
  :description "Retrieve info from twitter asynchronically"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.8.0"]
                 [twitter-api "1.8.0"]
                 [com.novemberain/monger "3.1.0"]
                 [cheshire "5.7.1"]]
  :main ^:skip-aot get-tweets.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all}})
